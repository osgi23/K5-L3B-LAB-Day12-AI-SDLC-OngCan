"""Phép thử độ bền không giao diện (Soak Headless, v1.3).

Lệnh: <soak_cmd> --seed 7 --days 10 --out soak.json
10 Ngày trong một tiến trình headless bằng bot tất định (hoặc --inputs).
Mỗi Ngày: gather -> quan -> shop.
Kế hoạch D1-D5 lặp ở Ngày 6-10.
Xuất: {"days": N, "days_completed": M, "crashes": 0, "results": [...], "duration_s": float}
Mỗi phần tử results[]: {"day": d, "earned": int, "reputation": float, "score": int}
"""

import argparse
import json
import math
import os
import sys
import tempfile
import time

from .contract import load_contract
from .errors import BadInput
from .ids import IdAllocator
from .inputs import InputPlayer, InputState, load_frames
from .rng import Streams
from .scenario import load_scenario
from .sim.day import DaySim


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


class DeterministicSoakBot:
    """Bot tất định điều khiển Út Sen qua chu kỳ Ngày hoàn chỉnh.
    
    - Sáng (gather): Bơi hái cây bông điên điển, bông súng rồi quay về cập bến an toàn.
    - Tối (quan): Phục vụ khách tại quán nếu có nguyên liệu nấu, di chuyển giữa bếp và bàn.
    - Đêm (shop): Mua nâng cấp hợp lý rồi chuyển ngày mới.
    """

    def __init__(self, tuning):
        self.tuning = tuning

    def decide_gather(self, sim, tick: int) -> InputState:
        # sim là GatherSim
        px, pd = sim.pos
        hold_count = len(sim.hold)
        hold_cap = sim.t["hold_capacity"]

        # Nếu đã hái được đồ hoặc qua tick 400 thì quay về bến [2, 0] cập bến
        if hold_count >= 2 or tick > 400:
            if sim._in_dock():
                return InputState((0.0, 0.0), {}, {"interact"})
            else:
                # Bơi về hướng bến [2, 0]
                dx = 2.0 - px
                dd = 0.0 - pd
                dist = math.hypot(dx, dd)
                if dist > 0.1:
                    return InputState((dx / dist, dd / dist), {}, set())
                else:
                    return InputState((0.0, 0.0), {}, {"interact"})
        else:
            # Tìm nút hái sẵn sàng gần nhất ở mặt nước
            ready_nodes = [n for n in sim.nodes if n["regrow_ticks"] == 0]
            if ready_nodes:
                target = min(ready_nodes, key=lambda n: math.dist(sim.pos, n["pos"]))
                dist = math.dist(sim.pos, target["pos"])
                if dist <= sim.t["interact_radius"]:
                    return InputState((0.0, 0.0), {}, {"interact"})
                else:
                    dx = target["pos"][0] - px
                    dd = target["pos"][1] - pd
                    d_len = math.hypot(dx, dd)
                    return InputState((dx / d_len, dd / d_len), {}, set())
            else:
                # Bơi thong thả mặt nước
                return InputState((1.0, 0.0), {}, set())

    def decide_quan(self, sim, tick: int) -> InputState:
        # sim là QuanSim
        px, pz = sim.pos
        irad = sim.t["interact_radius"]

        # 1. Nếu đang cầm món: đi giao bàn khách đang đợi
        if sim.hand is not None:
            waiting = [c for c in sim.customers if c["state"] == "waiting"]
            if waiting:
                # Tìm bàn của khách đang đợi
                target_c = waiting[0]
                target_tb = next((tb for tb in sim.tables if tb["id"] == target_c["table_id"]), None)
                if target_tb:
                    d = math.dist((px, pz), target_tb["pos"])
                    if d <= irad:
                        return InputState((0.0, 0.0), {}, {"interact"})
                    dx = target_tb["pos"][0] - px
                    dz = target_tb["pos"][1] - pz
                    d_len = math.hypot(dx, dz)
                    return InputState((dx / d_len, dz / d_len), {}, set())

        # 2. Nếu có bếp ready: đi lấy món
        ready_stoves = [st for st in sim.stoves if st["state"] == "ready"]
        if ready_stoves and sim.hand is None:
            st = ready_stoves[0]
            d = math.dist((px, pz), st["pos"])
            if d <= irad:
                return InputState((0.0, 0.0), {}, {"interact"})
            dx = st["pos"][0] - px
            dz = st["pos"][1] - pz
            d_len = math.hypot(dx, dz)
            return InputState((dx / d_len, dz / d_len), {}, set())

        # 3. Nếu có khách waiting và có bếp empty: thử đến bật bếp
        empty_stoves = [st for st in sim.stoves if st["state"] == "empty"]
        waiting_custs = [c for c in sim.customers if c["state"] == "waiting" and c.get("order_status") != "unfulfillable"]
        if empty_stoves and waiting_custs and sim.hand is None:
            st = empty_stoves[0]
            d = math.dist((px, pz), st["pos"])
            if d <= irad:
                return InputState((0.0, 0.0), {}, {"interact"})
            dx = st["pos"][0] - px
            dz = st["pos"][1] - pz
            d_len = math.hypot(dx, dz)
            return InputState((dx / d_len, dz / d_len), {}, set())

        # Đứng yên đợi khách / bếp
        return InputState((0.0, 0.0), {}, set())

    def decide_shop(self, sim, tick: int) -> InputState:
        # sim là ShopSim
        # Nếu có đủ tiền nâng cấp thì mua, không thì nhấn shop_done
        if sim.money >= 200 and sim.upgrades.get("oxygen", 0) < 1 and "oxygen" not in sim.bought_today:
            return InputState((0.0, 0.0), {}, set(), buy="oxygen")
        if sim.money >= 250 and sim.upgrades.get("hp", 0) < 1 and "hp" not in sim.bought_today:
            return InputState((0.0, 0.0), {}, set(), buy="hp")
        return InputState((0.0, 0.0), {}, {"shop_done"})

    def advance(self, day_sim, phase_tick: int) -> InputState:
        phase = day_sim.phase
        if phase == "gather":
            return self.decide_gather(day_sim.sub_sim, phase_tick)
        elif phase == "quan":
            return self.decide_quan(day_sim.sub_sim, phase_tick)
        elif phase == "shop":
            return self.decide_shop(day_sim.sub_sim, phase_tick)
        return InputState((0.0, 0.0), {}, set())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="chonoi.soak")
    parser.add_argument("--seed", type=_int("seed"), required=True)
    parser.add_argument("--days", type=_int("days"), default=10)
    parser.add_argument("--out", required=True)
    parser.add_argument("--inputs")
    parser.add_argument("--scenario")
    args = parser.parse_args(argv)

    start_time = time.perf_counter()

    if args.days < 1:
        sys.stderr.write("days phải >= 1\n")
        return 2

    contract = load_contract()
    tuning = contract["tuning"]
    scenario = load_scenario(args.scenario, "day", tuning) if args.scenario else {}
    frames = load_frames(args.inputs) if args.inputs else None

    streams = Streams(args.seed)
    ids = IdAllocator()
    day_sim = DaySim(tuning, scenario, streams, ids, days=args.days)

    input_source = InputPlayer(frames) if frames is not None else DeterministicSoakBot(tuning)

    results = []
    crashes = 0
    sim_tick = 0
    phase_tick = 0
    last_phase = day_sim.phase
    mult = tuning.get("score", {}).get("reputation_multiplier", 100)

    try:
        while not day_sim.done:
            if day_sim.phase != last_phase:
                phase_tick = 0
                last_phase = day_sim.phase

            if isinstance(input_source, InputPlayer):
                inp = input_source.advance(sim_tick)
            else:
                inp = input_source.advance(day_sim, phase_tick)

            # Trước khi bước, lưu ngày hiện tại
            curr_day = day_sim.day
            curr_phase = day_sim.phase

            evs = day_sim.step(inp)
            sim_tick += 1
            phase_tick += 1

            # Khi shop kết thúc và sang ngày mới (hoặc hoàn thành)
            if curr_phase == "shop" and (day_sim.phase != "shop" or day_sim.done):
                score = int(day_sim.earned + mult * math.floor(day_sim.reputation))
                results.append({
                    "day": curr_day,
                    "earned": day_sim.earned,
                    "reputation": round(day_sim.reputation, 3),
                    "score": score
                })

    except Exception as e:
        sys.stderr.write(f"Crash trong soak: {e}\n")
        crashes = 1

    duration_s = round(time.perf_counter() - start_time, 3)

    output_data = {
        "days": args.days,
        "days_completed": day_sim.days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": duration_s
    }

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=parent, prefix="soak_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, args.out)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise

    return 0 if crashes == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
