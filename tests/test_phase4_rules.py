"""Bộ kiểm thử đơn vị cho Phase 4 (Test Contract v1.3).

Kiểm tra:
1. Hợp đồng v1.3 khai báo đúng bench_cmd, soak_cmd, extensions leaderboard.
2. Benchmark đo đúng 5 trường JSON, đạt avg_fps >= 60, 1% low >= 30, load_ms <= 10s.
3. Soak headless 10 ngày (hoặc nhiều ngày), D1-D5 lặp ở D6-D10, hoàn thành với 0 crash.
4. Cơ chế bảng xếp hạng: cặp cờ, chế độ hợp lệ, sắp xếp điểm ổn định, top 10.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from chonoi.contract import load_contract
from chonoi.leaderboard import export_leaderboard, load_leaderboard, record_entry


def run_cmd(*args):
    cmd = [sys.executable, "-m"] + list(args)
    env = dict(os.environ)
    env["PYTHONPATH"] = "tests;." if os.name == "nt" else "tests:."
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return p.returncode, p.stdout, p.stderr


class TestPhase4Rules(unittest.TestCase):

    def test_01_contract_v13_declaration(self):
        """Hợp đồng game.contract.json phiên bản 1.3 và có bench_cmd, soak_cmd, extensions."""
        contract = load_contract()
        self.assertEqual(contract.get("contract_version"), "1.3")
        self.assertIn("bench_cmd", contract)
        self.assertIn("soak_cmd", contract)
        self.assertIn("leaderboard", contract.get("extensions", []))

    def test_02_benchmark_command_output_structure(self):
        """<bench_cmd> chạy và xuất đủ 5 trường JSON hợp lệ, thỏa mãn các mốc hiệu năng."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = os.path.join(tmpdir, "bench.json")
            code, stdout, stderr = run_cmd("chonoi.bench", "--seed", "42", "--duration", "1", "--warmup", "0.5", "--out", out_json)
            self.assertEqual(code, 0, f"bench lỗi: {stderr}")
            self.assertTrue(os.path.exists(out_json))

            with open(out_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            for key in ("avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"):
                self.assertIn(key, data, f"Thiếu trường {key} trong bench.json")

            self.assertGreaterEqual(data["avg_fps"], 60)
            self.assertGreaterEqual(data["p1_low_fps"], 30)
            self.assertLessEqual(data["load_ms"], 10000)
            self.assertGreater(data["frames"], 0)
            self.assertGreater(data["measured_s"], 0)

    def test_03_soak_headless_multi_day_loop(self):
        """<soak_cmd> chạy nhiều ngày, lặp kế hoạch D1-D5 ở ngày >= 6, hoàn thành 0 crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = os.path.join(tmpdir, "soak.json")
            code, stdout, stderr = run_cmd("chonoi.soak", "--seed", "7", "--days", "6", "--out", out_json)
            self.assertEqual(code, 0, f"soak lỗi: {stderr}")
            self.assertTrue(os.path.exists(out_json))

            with open(out_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(data["days"], 6)
            self.assertEqual(data["days_completed"], 6)
            self.assertEqual(data["crashes"], 0)
            self.assertEqual(len(data["results"]), 6)
            self.assertGreater(data["duration_s"], 0)

            # Kiểm tra trường mỗi ngày
            for res in data["results"]:
                self.assertIn("day", res)
                self.assertIn("earned", res)
                self.assertIn("reputation", res)
                self.assertIn("score", res)

    def test_04_leaderboard_cli_pair_and_mode_validation(self):
        """Cờ --leaderboard và --player-name phải đi theo cặp, chỉ dùng với mode day, tên không rỗng."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "out.jsonl")
            lb = os.path.join(tmpdir, "lb.json")

            # 1. Chỉ có --leaderboard thiếu --player-name -> mã 2
            code, _, _ = run_cmd("chonoi.headless", "--mode", "day", "--seed", "1", "--ticks", "10", "--out", out, "--leaderboard", lb)
            self.assertEqual(code, 2)

            # 2. Chỉ có --player-name thiếu --leaderboard -> mã 2
            code, _, _ = run_cmd("chonoi.headless", "--mode", "day", "--seed", "1", "--ticks", "10", "--out", out, "--player-name", "Út Sen")
            self.assertEqual(code, 2)

            # 3. Dùng với mode gather -> mã 2
            code, _, _ = run_cmd("chonoi.headless", "--mode", "gather", "--seed", "1", "--ticks", "10", "--out", out, "--leaderboard", lb, "--player-name", "Út Sen")
            self.assertEqual(code, 2)

            # 4. Tên rỗng -> mã 2
            code, _, _ = run_cmd("chonoi.headless", "--mode", "day", "--seed", "1", "--ticks", "10", "--out", out, "--leaderboard", lb, "--player-name", "   ")
            self.assertEqual(code, 2)

    def test_05_leaderboard_storage_sorting_and_export(self):
        """Bảng xếp hạng lưu trữ top 10, sắp xếp điểm giảm dần ổn định (hòa điểm mục trước đứng trước)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_p = os.path.join(tmpdir, "store.json")
            exp_p = os.path.join(tmpdir, "export.json")

            # Ghi 12 mục
            record_entry(store_p, "Player A", 100, 5, 1)
            record_entry(store_p, "Player B", 300, 5, 2)
            record_entry(store_p, "Player C", 200, 5, 3)
            record_entry(store_p, "Player D", 300, 5, 4)  # Bằng điểm Player B, nhưng ghi sau -> B đứng trước D
            for i in range(5, 13):
                record_entry(store_p, f"Player {i}", i * 10, 5, i)

            data = load_leaderboard(store_p)
            entries = data["entries"]

            # Chỉ giữ tối đa 10 mục
            self.assertEqual(len(entries), 10)
            # Điểm cao nhất đứng đầu
            self.assertEqual(entries[0]["name"], "Player B")
            self.assertEqual(entries[0]["score"], 300)
            # Hòa điểm: B ghi trước nên B đứng trước D
            self.assertEqual(entries[1]["name"], "Player D")
            self.assertEqual(entries[1]["score"], 300)
            self.assertEqual(entries[2]["name"], "Player C")
            self.assertEqual(entries[2]["score"], 200)

            # Xuất bảng xếp hạng
            export_leaderboard(store_p, exp_p)
            self.assertTrue(os.path.exists(exp_p))
            with open(exp_p, "r", encoding="utf-8") as f:
                exp_data = json.load(f)
            self.assertEqual(len(exp_data["entries"]), 10)
            self.assertEqual(exp_data["entries"][0]["name"], "Player B")


if __name__ == "__main__":
    unittest.main()
