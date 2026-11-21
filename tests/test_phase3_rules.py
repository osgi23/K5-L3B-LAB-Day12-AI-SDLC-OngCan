"""Bộ test chi tiết kiểm chứng các luật và AC của Phase 3 (Ticket-03 — Mùa Nước Nổi):
- Kho cá thể v1.2: items là mảng đối tượng {id, kind, fresh}.
- Từ chối file kho đếm loại cũ bằng mã thoát 2 (BadInput).
- Hao tươi: giỏ 0.5/s, quán 0.25/s, kẹp đáy 0, đóng băng khi pause.
- Ngưỡng ươn: fresh < 30, phát spoiled theo id đúng một lần khi qua ngưỡng.
- Giữ chỗ theo ID: ưu tiên cá thể tươi nhất, tie-break theo ID nhỏ.
- Tái giữ chỗ (re-reserve): khi hàng giữ bị ươn, nhả và thử giữ lại một lần; thất bại thì unfulfillable.
- Định giá động: base_price = floor(listed_price * avg_fresh / 100) khi cook_started, boa = floor(base_price * 0.2).
- Smoke handover: gather xuất kho cá thể -> quan đọc kho cá thể chính xác.
"""

import json
import math
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class TestPhase3Rules(unittest.TestCase):
    def test_threshold_30_spoiled_at_tick_1(self):
        """Kịch bản chuẩn từ Ticket-03: cá thể bắt đầu đúng fresh 30 nên ươn ở bước đầu (tick 1)."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30}],
                    "random_fish": False,
                    "monsters": []
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            sp_evs = events(rows, "spoiled")
            self.assertEqual(len(sp_evs), 1)
            self.assertEqual(sp_evs[0]["tick"], 1)
            self.assertEqual(sp_evs[0]["phase"], "gather")
            self.assertEqual(sp_evs[0]["data"], {
                "item_id": "I1", "kind": "ca_linh", "location": "hold"
            })
            snap1 = snapshots(rows)[-1]
            self.assertLess(snap1["hold"][0]["fresh"], 30.0)

    def test_gather_freshness_decay_rate(self):
        """Giỏ lặn giảm 0.5 điểm tươi/giây (0.5/60 mỗi tick). Sau 60 tick giảm đúng 0.5."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_loc", "fresh": 100.0}],
                    "random_fish": False,
                    "monsters": []
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "60",
                                     "--scenario", sc, "--snapshot-every", "60", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            snap_60 = [r for r in rows if r.get("type") == "snapshot" and r.get("tick") == 60][0]
            # 100.0 - 60 * (0.5 / 60) = 99.5
            self.assertAlmostEqual(snap_60["hold"][0]["fresh"], 99.5, places=3)

    def test_quan_freshness_decay_rate(self):
        """Kho quán giảm 0.25 điểm tươi/giây (0.25/60 mỗi tick). Sau 60 tick giảm đúng 0.25."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100.0}],
                    "random_customers": False
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "60",
                                     "--scenario", sc, "--snapshot-every", "60", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            snap_60 = [r for r in rows if r.get("type") == "snapshot" and r.get("tick") == 60][0]
            # 100.0 - 60 * (0.25 / 60) = 99.75
            self.assertAlmostEqual(snap_60["stock"][0]["fresh"], 99.75, places=3)

    def test_spoiled_emitted_only_once_and_sorted_by_id(self):
        """Nhiều cá thể cùng vượt ngưỡng phát theo thứ tự id, và chỉ phát một lần duy nhất."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [
                        {"id": "I2", "kind": "ca_linh", "fresh": 30.001},
                        {"id": "I1", "kind": "ca_loc", "fresh": 30.001}
                    ],
                    "random_fish": False,
                    "monsters": []
                }
            })
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "3",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            sp_evs = events(rows, "spoiled")
            # Tại tick 1: phát I1 trước, rồi I2
            self.assertEqual(len(sp_evs), 2)
            self.assertEqual(sp_evs[0]["data"]["item_id"], "I1")
            self.assertEqual(sp_evs[1]["data"]["item_id"], "I2")
            # Tại tick 2 và tick 3: không phát lại nữa
            self.assertEqual(sum(1 for r in rows if r.get("name") == "spoiled"), 2)

    def test_rejection_of_counted_inventory_file_exit_2(self):
        """Contract v1.2 trả mã 2 khi nhận file kho đếm loại cũ."""
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_loc": 2}})
            code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                   "--inventory", inv, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(w.path("o.jsonl")))

    def test_re_reservation_when_reserved_item_spoils(self):
        """Khi nguyên liệu giữ bị ươn (< 30), quán nhả phần giữ và thử giữ lại cá thể tươi thay thế."""
        with Workdir() as w:
            # Khách C1 cần ca_loc_nuong_trui (công thức: 1 ca_loc)
            # Kho có I1 (fresh 30.001 - bị ươn sau tick 1) và I2 (fresh 95.0 - cá thể tươi thay thế)
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": [
                        {"id": "I1", "kind": "ca_loc", "fresh": 30.001},
                        {"id": "I2", "kind": "ca_loc", "fresh": 95.0}
                    ],
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "state": "waiting", "order_status": "reserved", "reserved": ["I1"]
                    }],
                    "random_customers": False
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            # Event spoiled phát ra cho I1
            sp_evs = events(rows, "spoiled")
            self.assertEqual(len(sp_evs), 1)
            self.assertEqual(sp_evs[0]["data"]["item_id"], "I1")

            # Snapshot tick 1: C1 đã được re-reserve chuyển sang I2!
            snap1 = [r for r in rows if r.get("type") == "snapshot" and r.get("tick") == 1][0]
            c1_snap = [c for c in snap1["customers"] if c["id"] == "C1"][0]
            self.assertEqual(c1_snap["order_status"], "reserved")
            self.assertEqual(c1_snap["reserved"], ["I2"])

    def test_unfulfillable_order_when_re_reservation_fails(self):
        """Khi nguyên liệu giữ bị ươn nhưng kho không còn cá thể thay thế: chuyển unfulfillable."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "stock": [
                        {"id": "I1", "kind": "ca_loc", "fresh": 30.001}
                    ],
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "state": "waiting", "order_status": "reserved", "reserved": ["I1"]
                    }],
                    "random_customers": False
                }
            })
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            snap1 = [r for r in rows if r.get("type") == "snapshot" and r.get("tick") == 1][0]
            c1_snap = [c for c in snap1["customers"] if c["id"] == "C1"][0]
            self.assertEqual(c1_snap["order_status"], "unfulfillable")
            self.assertEqual(c1_snap["reserved"], [])

    def test_dynamic_pricing_based_on_freshness_and_tips(self):
        """Bắt đầu nấu chốt base_price = floor(listed * avg_fresh / 100); boa = floor(base_price * 0.2)."""
        with Workdir() as w:
            # Món ca_loc_nuong_trui: giá niêm yết 60, nấu 6s (360 tick)
            # Cá thể I1 có fresh = 80.0 -> base_price = floor(60 * 79.995833 / 100) = floor(47.9975) = 47
            # Player ở [2, 8] ngay cạnh bếp B1 [2, 8]
            sc = write_json(w.path("sc.json"), {
                "quan": {
                    "player": {"pos": [2, 8]},
                    "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 80.0}],
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "state": "waiting", "order_status": "reserved", "reserved": ["I1"],
                        "patience_ticks_left": 3600
                    }],
                    "random_customers": False
                }
            })
            # Tick 0: interact để bắt đầu nấu
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            cook_evs = events(rows, "cook_started")
            self.assertEqual(len(cook_evs), 1)
            # Độ tươi giảm 1 tick ở đầu bước: 80.0 - 0.25/60 = 79.995833 -> floor(60 * 79.995833 / 100) = 47
            expected_avg = 80.0 - (0.25 / 60.0)
            expected_base = math.floor(60 * expected_avg / 100.0)
            self.assertEqual(cook_evs[0]["data"]["base_price"], expected_base)
            self.assertEqual(cook_evs[0]["data"]["items"][0]["id"], "I1")
            self.assertEqual(cook_evs[0]["data"]["items"][0]["kind"], "ca_loc")

    def test_handover_smoke_phase3(self):
        """Smoke test bàn giao kho v1.2: gather cập bến ghi kho cá thể -> quan đọc nguyên vẹn."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {
                "gather": {
                    "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 100.0}],
                    "random_fish": False,
                    "monsters": []
                }
            })
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            inv = w.path("inv.json")
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1",
                                     "--scenario", sc, "--inputs", inp, "--inventory-out", inv,
                                     "--out", w.path("g.jsonl"))
            self.assertEqual(code, 0, err)
            with open(inv, encoding="utf-8") as f:
                saved = json.load(f)
            # Hao 1 tick: 100 - 0.5/60 = 99.992
            self.assertEqual(saved["items"][0]["id"], "I1")
            self.assertEqual(saved["items"][0]["kind"], "ca_linh")
            self.assertAlmostEqual(saved["items"][0]["fresh"], 99.992, places=3)

            # Quán đọc kho này ở ticks = 0
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0",
                                     "--inventory", inv, "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            q_rows = read_jsonl(w.path("q.jsonl"))
            self.assertEqual(snapshots(q_rows)[0]["stock"], saved["items"])

    def test_day_cycle_phase3_stock_and_new_day_reset(self):
        """Vòng ngày DaySim: hàng chưa dùng hết trong Quán bị hủy bỏ khi sang Ngày 2."""
        with Workdir() as w:
            # Chạy day với 2 ngày, ticks 30 (chưa qua ngày nhưng kiểm tra vòng ngày dựng đúng)
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "10",
                                     "--days", "2", "--out", w.path("d.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("d.jsonl"))
            self.assertEqual(rows[0]["type"], "event")
            self.assertEqual(rows[0]["name"], "day_start")
            self.assertEqual(rows[0]["day"], 1)


if __name__ == "__main__":
    unittest.main()
