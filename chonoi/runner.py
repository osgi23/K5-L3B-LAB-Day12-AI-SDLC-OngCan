"""Vòng tick (Contract B, mô hình tick, v1.1).

Thứ tự ghi: snapshot tick 0 -> với mỗi bước: sự kiện (theo thứ tự xử lý) rồi snapshot (nếu tới lượt
hoặc buổi kết thúc) -> dòng 'end'. Mỗi tick tối đa một snapshot.

`Session` là API bước tick gọn dùng chung cho headless (`run`) và cửa sổ chơi trực tiếp (`chonoi.live`):
cả hai chạy CÙNG một lớp sim, không nhân đôi logic.
"""

import math

from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.day import DaySim
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def build_sim(mode, tuning, scenario, seed, inventory, days=1):
    streams, ids = Streams(seed), IdAllocator()
    if mode == "gather":
        return GatherSim(tuning, scenario, streams, ids)
    elif mode == "quan":
        return QuanSim(tuning, scenario, streams, ids, inventory=inventory)
    elif mode == "day":
        return DaySim(tuning, scenario, streams, ids, days=days)
    from .errors import BadInput
    raise BadInput(f"mode không hợp lệ: {mode}")


def _common(sim, tick, sim_tick, phase_tick, tuning, state):
    mult = tuning["score"]["reputation_multiplier"]
    return {
        "type": "snapshot", "tick": tick, "sim_tick": sim_tick, "mode": sim.mode, "phase": sim.phase,
        "phase_tick": phase_tick, "state": state, "time_left_ticks": sim.time_left_ticks,
        "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
        "score": sim.earned + mult * math.floor(sim.reputation),
    }


class Session:
    """Một lượt chơi: dựng sim, bước từng tick, lấy snapshot / dòng end."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, days=1):
        self.mode = mode
        self.tuning = tuning
        self.sim = build_sim(mode, tuning, scenario, seed, inventory, days=days)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False

    @property
    def done(self) -> bool:
        return self.sim.done

    def snapshot(self) -> dict:
        phase_tick = self.sim.phase_tick if hasattr(self.sim, "phase_tick") else self.tick
        state = "paused" if self.paused else ("finished" if self.sim.done else "playing")
        s = _common(self.sim, self.tick, self.sim_tick, phase_tick, self.tuning, state)
        s.update(self.sim.snapshot())
        return s

    def initial_event_rows(self) -> list:
        if hasattr(self.sim, "initial_events"):
            return self._format_events(self.sim.initial_events(), tick_override=0)
        return []

    def _format_events(self, events: list, tick_override=None) -> list:
        t = self.tick if tick_override is None else tick_override
        rows = []
        for ev in events:
            if len(ev) == 2:
                phase = self.sim.phase
                name, data = ev[0], ev[1]
                day = getattr(self.sim, "day", None)
            elif len(ev) == 3:
                phase, name, data = ev[0], ev[1], ev[2]
                day = getattr(self.sim, "day", None)
            else:
                phase, name, data, day = ev[0], ev[1], ev[2], ev[3]
            row = {"type": "event", "tick": t, "phase": phase, "name": name, "data": data}
            if self.mode == "day" and day is not None:
                row["day"] = day
            rows.append(row)
        return rows

    def step(self, inp) -> list:
        """Chạy một bước với `inp` (chonoi.inputs.InputState); trả các dòng event."""
        # 1. Xét cạnh pause trước
        if not self.paused:
            if inp.pressed("pause"):
                self.paused = True
                self.tick += 1
                return self._format_events([("paused", {})])
        else:
            # Đang pause
            if inp.pressed("pause"):
                self.paused = False
                # Cạnh lên tiếp theo phát resumed, chạy gameplay ngay trong bước đó
                sim_events = self.sim.step(inp)
                self.tick += 1
                self.sim_tick += 1
                all_evs = [("resumed", {})]
                all_evs.extend(sim_events)
                return self._format_events(all_evs)
            else:
                # Vẫn đang pause: bỏ qua input hành động
                self.tick += 1
                return []

        # 2. Bước gameplay bình thường
        events = self.sim.step(inp)
        self.tick += 1
        self.sim_tick += 1
        return self._format_events(events)

    def end_row(self) -> dict:
        sim = self.sim
        phase_tick = getattr(sim, "phase_tick", self.tick)
        score = _common(sim, self.tick, self.sim_tick, phase_tick, self.tuning, "")["score"]
        row = {
            "type": "end", "ticks": self.tick, "sim_tick": self.sim_tick, "mode": sim.mode,
            "state": "finished" if sim.done else "playing",
            "reason": sim.reason if sim.done else "tick_limit",
            "money": sim.money, "earned": sim.earned, "reputation": sim.reputation, "score": score
        }
        if self.mode == "day":
            row["days_completed"] = getattr(sim, "days_completed", 0)
        return row

    def write_inventory_if_done(self, inventory_out):
        """File kho: ghi MỘT lần khi có gather_end; chưa kết thúc thì giữ nguyên file đích."""
        if self.mode == "gather" and self.sim.done and inventory_out:
            write_inventory(inventory_out, self.sim.inventory_items())


def run(mode, tuning, scenario, seed, frames, ticks, out_path, snapshot_every,
        inventory=None, inventory_out=None, days=1):
    sess = Session(mode, tuning, scenario, seed, inventory, days=days)
    player = InputPlayer(frames)
    w = JsonlWriter(out_path)
    try:
        # Tick 0: initial events (nếu có, e.g. day_start, day_plan, phase_start)
        for row in sess.initial_event_rows():
            w.write(row)
        w.write(sess.snapshot())  # tick 0: sau khi dựng scenario, trước mọi input
        last_snapped = 0
        while sess.tick < ticks and not sess.done:
            inp = player.advance(sess.tick)  # bước k đọc input có tick == k
            for row in sess.step(inp):
                w.write(row)
            if sess.tick % snapshot_every == 0 or sess.done:
                w.write(sess.snapshot())
                last_snapped = sess.tick
        if last_snapped != sess.tick:
            w.write(sess.snapshot())
        w.write(sess.end_row())
    finally:
        w.close()
    sess.write_inventory_if_done(inventory_out)
    return sess.sim
