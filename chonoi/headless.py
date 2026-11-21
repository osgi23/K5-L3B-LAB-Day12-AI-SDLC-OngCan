"""Điểm vào headless: python3 -m chonoi.headless --mode gather --seed 1 --ticks 600 --out out.jsonl

Mã thoát: 0 bình thường; 2 tham số/đầu vào sai (kiểm TRƯỚC khi ghi đầu ra); 1 lỗi chạy/ghi.
"""

import argparse
import math
import os
import sys

from .contract import load_contract
from .errors import BadInput
from .inputs import load_frames
from .inventory import read_inventory
from .leaderboard import export_leaderboard, record_entry
from .runner import run
from .scenario import load_scenario


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


def main(argv=None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if "--export-leaderboard" in args_list:
        p_exp = argparse.ArgumentParser(add_help=False)
        p_exp.add_argument("--export-leaderboard", dest="export_leaderboard")
        p_exp.add_argument("--leaderboard")
        exp_args, _ = p_exp.parse_known_args(args_list)
        try:
            export_leaderboard(exp_args.leaderboard or "leaderboard.json", exp_args.export_leaderboard)
            return 0
        except Exception as e:
            sys.stderr.write(f"lỗi xuất bảng xếp hạng: {e}\n")
            return 1

    p = _Parser(prog="chonoi.headless")
    p.add_argument("--mode", required=True, choices=["gather", "quan", "day"])  # `day` có từ v1.1
    p.add_argument("--seed", required=True, type=_int("seed"))
    p.add_argument("--ticks", required=True, type=_int("ticks"))
    p.add_argument("--out", required=True)
    p.add_argument("--scenario")
    p.add_argument("--inputs")
    p.add_argument("--inventory")
    p.add_argument("--inventory-out", dest="inventory_out")
    p.add_argument("--days", type=_int("days"), default=None)
    p.add_argument("--snapshot-every", dest="snapshot_every", type=_int("snapshot-every"), default=10)
    p.add_argument("--leaderboard", help="file lưu bảng xếp hạng")
    p.add_argument("--player-name", dest="player_name", help="tên người chơi cho bảng xếp hạng")
    p.add_argument("--export-leaderboard", dest="export_leaderboard", help="xuất bảng xếp hạng ra file json")
    a = p.parse_args(argv)
    if a.export_leaderboard:
        try:
            export_leaderboard(a.leaderboard or "leaderboard.json", a.export_leaderboard)
            return 0
        except Exception as e:
            sys.stderr.write(f"lỗi xuất bảng xếp hạng: {e}\n")
            return 1
    try:
        has_lb = a.leaderboard is not None
        has_pn = a.player_name is not None
        if (has_lb and not has_pn) or (has_pn and not has_lb):
            raise BadInput("thiếu một cờ trong cặp --leaderboard và --player-name")
        if (has_lb or has_pn) and a.mode != "day":
            raise BadInput("--leaderboard và --player-name chỉ dùng với mode day")
        if has_pn and (not isinstance(a.player_name, str) or not a.player_name.strip()):
            raise BadInput("player-name không được rỗng")
        days = a.days if a.days is not None else 1
        if a.days is not None and a.mode != "day":
            raise BadInput("--days chỉ dùng với mode day")
        if a.mode == "day":
            if days < 1 or days > 5:
                raise BadInput("--days phải trong khoảng 1 đến 5")
            if a.inventory or a.inventory_out:
                raise BadInput("--inventory và --inventory-out không dùng với mode day")
        if a.ticks < 0:
            raise BadInput("--ticks phải >= 0")
        if a.snapshot_every <= 0:
            raise BadInput("--snapshot-every phải > 0")
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        outs = [x for x in (a.out, a.inventory_out) if x]
        ins = [x for x in (a.scenario, a.inputs, a.inventory) if x]
        paths = [os.path.abspath(x) for x in outs + ins]
        if len(set(paths)) != len(paths):
            raise BadInput("các đường dẫn đầu vào/đầu ra phải khác nhau")
        contract = load_contract()
        tuning = contract["tuning"]
        scenario = load_scenario(a.scenario, a.mode, tuning)
        frames = load_frames(a.inputs)
        inventory = read_inventory(a.inventory) if a.inventory else None
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    try:
        sim = run(a.mode, tuning, scenario, a.seed, frames, a.ticks, a.out, a.snapshot_every,
                  inventory=inventory, inventory_out=a.inventory_out, days=days)
        if has_lb and has_pn:
            if a.scenario is None and days == 5 and getattr(sim, "reason", "") == "days_complete" and getattr(sim, "days_completed", 0) == 5:
                mult = tuning.get("score", {}).get("reputation_multiplier", 100)
                final_score = int(sim.earned + mult * math.floor(sim.reputation))
                record_entry(a.leaderboard, a.player_name, final_score, 5, a.seed)
    except BadInput as e:  # lỗi mức luật phát hiện lúc dựng sim
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
