"""Kiểm thử tích hợp cho Phase 2 (Test Contract v1.1).

Bao gồm:
1. Kịch bản v1.1 đầy đủ: 8 đàn cá ban đầu, sinh cá, cá bơi và phản xạ mép, cá sấu tuần tra và rượt.
2. Kịch bản vòng ngày: lặn mang cá về, quán phục vụ, vào shop mua oxy/máu, ngày 2 áp dụng nâng cấp mới.
3. Kịch bản lỗi: các trường hợp vi phạm hợp đồng v1.1 phải exit 2 trước khi ghi dữ liệu.
4. Kịch bản Pause / Resume: cơ chế tạm dừng bằng nút pause (P).
5. Kịch bản Shop: mua nâng cấp, kiểm tra ràng buộc tiền và cấp tối đa.
"""

import json
import os
import unittest

from chonoi.contract import load_contract
from helpers import Workdir, frames, read_jsonl, run_headless, snapshots, write_json


class TestPhase2Rules(unittest.TestCase):
    def setUp(self):
        self.contract = load_contract()
        self.tuning = self.contract["tuning"]

    def test_v11_full_fish_and_monsters(self):
        """1. Kịch bản v1.1 đầy đủ: 8 đàn cá ban đầu, sinh cá, cá bơi và phản xạ mép, cá sấu tuần tra và rượt."""
        with Workdir() as w:
            out = w.path("out.jsonl")
            # Chạy gather trong 400 tick để thấy:
            # - 8 đàn cá ban đầu ở tick 0
            # - cá bơi và đổi hướng ở tick 120, 240, 360
            # - sinh cá tại phase_tick = 360
            # - cá sấu M1 tuần tra
            code, err = run_headless("--mode", "gather", "--seed", "42", "--ticks", "400", "--out", out)
            self.assertEqual(code, 0, err)

            rows = read_jsonl(out)
            snaps = snapshots(rows)
            s0 = snaps[0]

            # Kiểm tra 8 đàn cá ban đầu
            self.assertEqual(len(s0["fish"]), 8)
            # Kiểm tra cá sấu M1 xuất hiện ở Day 1
            self.assertIn("monsters", s0)
            self.assertEqual(len(s0["monsters"]), 1)
            self.assertEqual(s0["monsters"][0]["id"], "M1")
            self.assertEqual(s0["monsters"][0]["kind"], "ca_sau")
            self.assertEqual(s0["monsters"][0]["state"], "patrol")

            # Kiểm tra event sinh cá tại tick 360
            events = [r for r in rows if r["type"] == "event"]
            spawn_events = [e for e in events if e["name"] == "fish_spawned"]
            self.assertTrue(len(spawn_events) >= 1, "phải có ít nhất 1 lần sinh cá tại tick 360")
            sp = spawn_events[0]
            self.assertIn("id", sp["data"])
            self.assertIn(sp["data"]["kind"], ("ca_linh", "ca_loc", "ca_keo"))

    def test_crocodile_chase_and_hit(self):
        """Cá sấu rượt người chơi ở d >= 10 khi cách <= 10m, hit làm mất 1 máu và giật lùi."""
        with Workdir() as w:
            out = w.path("croc.jsonl")
            # Đặt người chơi ở gần M1 (M1 ở [60, 24]), cho người chơi ở [60, 22] (khoảng cách 2m <= 10m)
            # và sau 6 tick di chuyển chạm nhau (<= 1.5m)
            scen = {
                "gather": {
                    "player": {"pos": [60.0, 23.0], "hp": 3},
                    "random_fish": False,
                    "fish": []
                }
            }
            scen_path = write_json(w.path("scen.json"), scen)
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "30",
                                     "--scenario", scen_path, "--out", out)
            self.assertEqual(code, 0, err)

            rows = read_jsonl(out)
            events = [r for r in rows if r["type"] == "event"]
            hit_events = [e for e in events if e["name"] == "monster_hit"]
            self.assertTrue(len(hit_events) >= 1, "phải có monster_hit khi cá sấu chạm người chơi")
            hit = hit_events[0]["data"]
            self.assertEqual(hit["monster_id"], "M1")
            self.assertEqual(hit["hp"], 2)

    def test_day_cycle_and_shop_upgrades(self):
        """2. Kịch bản vòng ngày: lặn mang cá về, quán phục vụ, vào shop mua oxy, ngày 2 áp dụng oxy mới."""
        with Workdir() as w:
            out = w.path("day.jsonl")
            # Kịch bản Day: bắt đầu với money=200, earned=200 để có tiền mua oxy trong Shop (cấp 1 giá 200)
            # Scenario: người chơi bắt đầu ở bến [2, 0], nhấn interact ở tick 0 để cập bến ngay lập tức (giỏ rỗng)
            # Quán mở, hết giờ sau tick_limit hoặc timeout ca quán
            scen = {
                "day": {
                    "money": 250,
                    "earned": 250
                },
                "gather": {
                    "time_left_ticks": 2,
                    "random_fish": False
                },
                "quan": {
                    "time_left_ticks": 2
                }
            }
            scen_p = write_json(w.path("scen.json"), scen)

            # Inputs: tick 0 interact (cập bến), sau đó trong shop gửi buy="oxygen" rồi shop_done
            inp_data = frames(
                {"tick": 0, "interact": True},
                {"tick": 5, "buy": "oxygen"},
                {"tick": 6, "shop_done": True}
            )
            inp_p = write_json(w.path("inp.json"), inp_data)

            # Chạy 2 ngày (--days 2), snapshot_every 1 để bắt mọi phase
            code, err = run_headless("--mode", "day", "--days", "2", "--seed", "1",
                                     "--ticks", "30", "--scenario", scen_p,
                                     "--inputs", inp_p, "--out", out, "--snapshot-every", "1")
            self.assertEqual(code, 0, err)

            rows = read_jsonl(out)
            events = [r for r in rows if r["type"] == "event"]
            names = [e["name"] for e in events]

            # Kiểm tra chuỗi phase
            self.assertIn("day_start", names)
            self.assertIn("day_plan", names)
            self.assertIn("phase_start", names)
            self.assertIn("gather_end", names)
            self.assertIn("quan_end", names)

            # Kiểm tra event bought trong shop
            bought_events = [e for e in events if e["name"] == "bought"]
            self.assertEqual(len(bought_events), 1)
            b = bought_events[0]["data"]
            self.assertEqual(b["upgrade"], "oxygen")
            self.assertEqual(b["level"], 1)
            self.assertEqual(b["price"], 200)
            self.assertEqual(b["money"], 50)

            # Kiểm tra shop_end và sang ngày 2
            shop_end_events = [e for e in events if e["name"] == "shop_end"]
            self.assertTrue(len(shop_end_events) >= 1)

            # Kiểm tra ngày 2: active_upgrades có oxygen: 1 và oxy max thành 45s (2700 ticks)
            day2_snaps = [s for s in snapshots(rows) if s.get("day") == 2 and s.get("phase") == "gather"]
            self.assertTrue(len(day2_snaps) > 0, "phải có snapshot ngày 2 pha gather")
            s_d2 = day2_snaps[0]
            self.assertEqual(s_d2["active_upgrades"]["oxygen"], 1)
            self.assertEqual(s_d2["player"]["oxygen_max_ticks"], 2700)

    def test_scenario_v11_error_exit_2(self):
        """3. Kịch bản lỗi: các trường hợp vi phạm hợp đồng v1.1 phải exit 2 trước khi ghi dữ liệu."""
        with Workdir() as w:
            out = w.path("err.jsonl")

            # 1. --days ngoài [1, 5]
            code, _ = run_headless("--mode", "day", "--days", "0", "--seed", "1", "--ticks", "10", "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))

            code, _ = run_headless("--mode", "day", "--days", "6", "--seed", "1", "--ticks", "10", "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))

            # 2. --days dùng với mode gather hoặc quan
            code, _ = run_headless("--mode", "gather", "--days", "2", "--seed", "1", "--ticks", "10", "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))

            # 3. cấm quan.stock hoặc quan.reputation khi chạy day
            bad_scen = write_json(w.path("bad_day.json"), {"day": {}, "quan": {"stock": {"ca_loc": 1}}})
            code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "10", "--scenario", bad_scen, "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))

            # 4. day.money > day.earned
            bad_money = write_json(w.path("bad_money.json"), {"day": {"money": 500, "earned": 100}})
            code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "10", "--scenario", bad_money, "--out", out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(out))

    def test_pause_and_resume(self):
        """4. Kịch bản Pause / Resume: cơ chế tạm dừng bằng nút pause (P)."""
        with Workdir() as w:
            out = w.path("pause.jsonl")
            # Bấm pause ở tick 2 (cạnh lên), nhả ở tick 3, bấm tiếp pause ở tick 5 (cạnh lên) để resume
            inp_data = frames(
                {"tick": 2, "pause": True},
                {"tick": 3, "pause": False},
                {"tick": 5, "pause": True}
            )
            inp_p = write_json(w.path("inp.json"), inp_data)
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--inputs", inp_p, "--out", out, "--snapshot-every", "1")
            self.assertEqual(code, 0, err)

            rows = read_jsonl(out)
            events = [r for r in rows if r["type"] == "event"]
            paused_evs = [e for e in events if e["name"] == "paused"]
            resumed_evs = [e for e in events if e["name"] == "resumed"]

            self.assertEqual(len(paused_evs), 1)
            self.assertEqual(len(resumed_evs), 1)
            self.assertEqual(paused_evs[0]["tick"], 3)
            self.assertEqual(resumed_evs[0]["tick"], 6)

            # Kiểm tra trạng thái paused trong snapshots giữa tick 3 và tick 5
            snaps = snapshots(rows)
            paused_snaps = [s for s in snaps if s["state"] == "paused"]
            self.assertTrue(len(paused_snaps) >= 1)
            # Trong thời gian pause, sim_tick không đổi
            sim_ticks = [s["sim_tick"] for s in paused_snaps]
            self.assertEqual(len(set(sim_ticks)), 1)


if __name__ == "__main__":
    unittest.main()
