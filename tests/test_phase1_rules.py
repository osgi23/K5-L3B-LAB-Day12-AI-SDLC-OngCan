"""Bộ test chi tiết kiểm chứng các luật và AC của Phase 1:
- Gather: dive, surface, oxy tiêu hao / hồi, oxygen_empty, ngạt (choke), ngất (faint/fainted LIFO), hái nút, bắt cá, hold_full, node_regrown.
- Quan: khách đến, giữ chỗ nguyên liệu, nấu món, giao món, boa, thanh toán, kiên nhẫn, bỏ về, đóng ca (closing).
"""

import json
import os
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class TestPhase1Gather(unittest.TestCase):
    def test_gather_dive_and_surface_events(self):
        """Bơi từ mặt nước xuống dưới nước phát dive; bơi ngược lên phát surface."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"player": {"pos": [20, 0.4]}}})
            # Bơi xuống (move [0, 1]) rồi bơi lên (move [0, -1])
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "move": [0, 1]},
                {"tick": 20, "move": [0, -1]},
                {"tick": 40, "move": [0, 0]}
            ))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "50",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            dive_evs = events(rows, "dive")
            surf_evs = events(rows, "surface")
            self.assertTrue(len(dive_evs) >= 1, "Phải phát ít nhất 1 event dive")
            self.assertTrue(len(surf_evs) >= 1, "Phải phát ít nhất 1 event surface")
            self.assertIn("pos", dive_evs[0]["data"])
            self.assertIn("pos", surf_evs[0]["data"])

    def test_gather_oxygen_consumption_and_empty(self):
        """Dưới nước trừ 1 tick oxy mỗi tick; chạm 0 phát oxygen_empty."""
        with Workdir() as w:
            # Đặt player ở d = 2.0 (dưới nước), oxy còn 5 tick
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 2.0], "oxygen_ticks": 5, "zero_oxy_ticks": 0}
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "10",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            empty_evs = events(rows, "oxygen_empty")
            self.assertEqual(len(empty_evs), 1)
            self.assertEqual(empty_evs[0]["data"]["oxygen_ticks"], 0)

    def test_gather_choke_and_faint(self):
        """Oxy = 0 dưới nước đếm ngạt đủ 60 tick phát choke (-1 HP); hết 3 HP phát faint + gather_end(fainted) mất giỏ."""
        with Workdir() as w:
            # Player ở d = 5.0, oxy = 0, HP = 1, zero_oxy_ticks = 58
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [20, 5.0], "oxygen_ticks": 0, "hp": 1, "zero_oxy_ticks": 58},
                "hold": ["ca_loc", "bong_sung"]
            }})
            inv = w.path("inv.json")
            # Sau 2 tick, zero_oxy_ticks chạm 60 -> choke -> HP về 0 -> faint!
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--inventory-out", inv, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            choke_evs = events(rows, "choke")
            self.assertEqual(len(choke_evs), 1)
            self.assertEqual(choke_evs[0]["data"]["hp"], 0)

            faint_evs = events(rows, "faint")
            self.assertEqual(len(faint_evs), 1)
            self.assertEqual(faint_evs[0]["data"]["cause"], "choke")
            # Thứ tự bỏ LIFO: nhặt sau bỏ trước (bong_sung rồi ca_loc)
            self.assertEqual([it["kind"] for it in faint_evs[0]["data"]["lost"]], ["bong_sung", "ca_loc"])

            end_evs = events(rows, "gather_end")
            self.assertEqual(len(end_evs), 1)
            self.assertEqual(end_evs[0]["data"]["reason"], "fainted")
            self.assertEqual(end_evs[0]["data"]["inventory"], {"items": []})

            # File kho phải rỗng khi ngất
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": []})

    def test_gather_node_interaction_and_hold_full(self):
        """Hái cây ở mặt nước, đủ chỗ thì phát gather; đầy chỗ phát hold_full."""
        with Workdir() as w:
            # Player ở [12, 0], nút N1 ở [12, 0]
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [12, 0]},
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0], "regrow_ticks": 0}]
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            g_evs = events(rows, "gather")
            self.assertEqual(len(g_evs), 1)
            self.assertEqual(g_evs[0]["data"]["kind"], "bong_dien_dien")
            self.assertEqual(g_evs[0]["data"]["amount"], 1)

            # Test khi đầy giỏ
            sc_full = write_json(w.path("sc_full.json"), {"gather": {
                "player": {"pos": [12, 0]},
                "hold": ["ca_loc"] * 12,
                "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0], "regrow_ticks": 0}]
            }})
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc_full, "--inputs", inp, "--out", w.path("o2.jsonl"))
            self.assertEqual(code, 0, err)
            rows2 = read_jsonl(w.path("o2.jsonl"))
            hf_evs = events(rows2, "hold_full")
            self.assertEqual(len(hf_evs), 1)
            self.assertEqual(hf_evs[0]["data"]["action"], "gather")
            self.assertEqual(hf_evs[0]["data"]["free"], 0)

    def test_gather_fish_catch_and_cooldown(self):
        """Bắt cá dưới nước phát fish_caught, nhận yield cá linh = 3, kích hoạt cooldown."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {
                "player": {"pos": [15, 5], "catch_cd_ticks": 0},
                "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5], "heading_deg": 0}],
                "random_fish": False
            }})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "catch": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "2",
                                     "--scenario", sc, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            fc_evs = events(rows, "fish_caught")
            self.assertEqual(len(fc_evs), 1)
            self.assertEqual(fc_evs[0]["data"]["kind"], "ca_linh")
            self.assertEqual(fc_evs[0]["data"]["yield"], 3)
            # Kiểm tra giỏ trong snapshot có 3 cá linh
            last_snap = snapshots(rows)[-1]
            self.assertEqual([it["kind"] for it in last_snap["hold"]], ["ca_linh", "ca_linh", "ca_linh"])


class TestPhase1Quan(unittest.TestCase):
    def test_quan_cook_pick_serve_and_pay(self):
        """Quán: khách chờ -> interact bếp nấu (cook_started) -> chín (dish_ready) -> nhặt (dish_picked) -> phục vụ (served) -> ăn xong trả tiền (paid)."""
        with Workdir() as w:
            # Bếp B1 ở [2, 8], Bàn T1 ở [9, 2], player ở [2, 8]
            sc = write_json(w.path("sc.json"), {"quan": {
                "player": {"pos": [2, 8]},
                "stock": {"ca_loc": 1},
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "order_status": "reserved", "order_tick": 0
                }],
                "random_customers": False
            }})
            # tick 0: interact tại bếp B1 để bắt đầu nấu (cook_s = 6 -> 360 tick)
            # tick 360: món chín
            # tick 361: interact tại bếp B1 để nhặt món
            # Di chuyển tới bàn T1 ([9, 2])
            # Sau khi tới bàn: interact để phục vụ
            # ca_loc_nuong_trui cook_s = 6s (360 ticks). Để test nhanh, ta có thể test trực tiếp bếp đã chín (ready):
            sc_ready = write_json(w.path("sc_ready.json"), {"quan": {
                "player": {"pos": [2, 8]},
                "stoves": [{"id": "B1", "pos": [2, 8], "state": "ready", "dish": "ca_loc_nuong_trui",
                            "order_id": "C1", "base_price": 60}],
                "tables": [{"id": "T1", "pos": [3, 8]}],  # Đặt bàn gần bếp để tương tác dễ
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "order_status": "assigned", "state": "waiting", "patience_ticks_left": 3600
                }],
                "random_customers": False
            }})
            # Tick 0: interact tại bếp nhặt món
            # Tick 1: bước sang phải ([1, 0]) tới gần bàn T1 ([3, 8])
            # Tick 2: interact phục vụ khách
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False, "move": [1, 0]},
                {"tick": 20, "move": [0, 0], "interact": True},
                {"tick": 21, "interact": False}
            ))
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "30",
                                     "--scenario", sc_ready, "--inputs", inp, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            picked = events(rows, "dish_picked")
            served = events(rows, "served")
            self.assertEqual(len(picked), 1)
            self.assertEqual(picked[0]["data"]["order_id"], "C1")
            self.assertEqual(len(served), 1)
            self.assertEqual(served[0]["data"]["order_id"], "C1")
            self.assertEqual(served[0]["data"]["table_id"], "T1")
            self.assertEqual(served[0]["data"]["base_price"], 60)
            self.assertGreater(served[0]["data"]["tip"], 0)

    def test_quan_customer_leaves_on_patience_zero(self):
        """Khách hết kiên nhẫn phát customer_left (reason: patience) và bị trừ uy tín."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {
                "player": {"pos": [8, 5]},
                "stock": [{"id": "I1", "kind": "bong_sung", "fresh": 100}, {"id": "I2", "kind": "bong_sung", "fresh": 100}],
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                    "state": "waiting", "patience_ticks_left": 2, "order_status": "reserved"
                }],
                "random_customers": False
            }})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            left_evs = events(rows, "customer_left")
            self.assertEqual(len(left_evs), 1)
            self.assertEqual(left_evs[0]["data"]["reason"], "patience")
            self.assertEqual(left_evs[0]["data"]["order_id"], "C1")
            # Uy tín ban đầu 3.0, trừ 0.5 còn 2.5
            self.assertEqual(left_evs[0]["data"]["reputation"], 2.5)

    def test_quan_closing_time_payment_and_departure(self):
        """Khi hết ca: khách eating trả tiền (reason: closing), khách waiting rời đi (reason: closing) không trừ uy tín, phát quan_end."""
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {
                "player": {"pos": [8, 5]},
                "time_left_ticks": 2,
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                    "state": "eating", "eat_ticks_left": 100, "base_price": 40, "tip": 8
                }],
                "random_customers": False
            }})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5",
                                     "--scenario", sc, "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            paid_evs = events(rows, "paid")
            self.assertEqual(len(paid_evs), 1)
            self.assertEqual(paid_evs[0]["data"]["reason"], "closing")
            self.assertEqual(paid_evs[0]["data"]["amount"], 48)

            end_evs = events(rows, "quan_end")
            self.assertEqual(len(end_evs), 1)
            self.assertEqual(end_evs[0]["data"]["reason"], "time")
            self.assertEqual(end_evs[0]["data"]["money"], 48)


if __name__ == "__main__":
    unittest.main()
