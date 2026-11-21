# Ma trận truy vết Phase 3 (Ticket-03 — Change Request “Mùa Nước Nổi”, Test Contract v1.2)

| AC | Nội dung yêu cầu | Cách kiểm chứng | Bằng chứng (link file proof) | Kết quả |
|---|---|---|---|---|
| **AC-P3-01** | Test Contract v1.2 & tuning `freshness` (initial 100, gather 0.5, quan 0.25, spoiled 30) | Kiểm tra `game.contract.json`, `chonoi/contract.py` | [test.log](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-3/test.log) | **Đạt** |
| **AC-P3-02** | Kho cá thể `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}` | Kiểm tra schema file kho và sự kiện `gather_end` | [catch.json](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-3/catch.json), `test_inv_01_*` | **Đạt** |
| **AC-P3-03** | Từ chối file kho đếm loại cũ và sai schema với exit code 2 (`BadInput`) | Chạy quan với file kho đếm cũ `{"items": {"ca_loc": 2}}` | `test_rejection_of_counted_inventory_file_exit_2` | **Đạt** |
| **AC-P3-04** | Cấp phát ID `I1, I2, ...` tuần tự, tăng dần theo thứ tự vào giỏ và duy nhất xuyên pha | Unit test cấp phát id và kiểm tra thứ tự cá thể | `test_id_allocator_continues_after_max`, `test_phase3_rules` | **Đạt** |
| **AC-P3-05** | Hao tươi giỏ lặn 0.5/s (0.5/60 mỗi tick), kẹp đáy 0 | Đo độ tươi sau 60 tick lặn, kiểm tra giảm đúng 0.5 điểm | `test_gather_freshness_decay_rate` | **Đạt** |
| **AC-P3-06** | Hao tươi kho quán 0.25/s (0.25/60 mỗi tick), bao gồm cả hàng đang giữ | Đo độ tươi sau 60 tick mở quán, kiểm tra giảm đúng 0.25 điểm | `test_quan_freshness_decay_rate` | **Đạt** |
| **AC-P3-07** | Đóng băng hao tươi khi pause, không hao trong Shop và khi đang nấu | Kiểm tra snapshot qua các tick pause/shop | `test_pause_and_resume`, `test_day_cycle_phase3_stock_and_new_day_reset` | **Đạt** |
| **AC-P3-08** | Ngưỡng ươn `fresh < 30`, phát event `spoiled` theo ID đúng 1 lần khi vượt ngưỡng | Scenario bắt đầu tại `fresh: 30`, phát `spoiled` ở tick 1 | `test_threshold_30_spoiled_at_tick_1`, `test_spoiled_emitted_only_once_and_sorted_by_id` | **Đạt** |
| **AC-P3-09** | Cá thể ươn (`fresh < 30`) vẫn chiếm chỗ nhưng không được dùng để nấu | Kiểm tra lọc nguyên liệu khả dụng khi giữ chỗ và nấu | `test_phase3_rules.py` | **Đạt** |
| **AC-P3-10** | Giữ chỗ theo ID: ưu tiên cá thể tươi nhất, tie-break theo ID nhỏ hơn | Kiểm tra phân bổ ID cho đơn khách mới và đơn kịch bản | `test_phase3_rules.py` | **Đạt** |
| **AC-P3-11** | Tái giữ chỗ: khi hàng giữ bị ươn, nhả toàn bộ và thử giữ lại cá thể tươi thay thế | Kiểm tra re-reserve sang cá thể tươi còn lại trong kho | `test_re_reservation_when_reserved_item_spoils` | **Đạt** |
| **AC-P3-12** | Khi re-reserve thất bại, chuyển trạng thái đơn sang `unfulfillable` | Kiểm tra đơn chuyển unfulfillable, khách chờ tới hết kiên nhẫn | `test_unfulfillable_order_when_re_reservation_fails` | **Đạt** |
| **AC-P3-13** | Định giá động: `base_price = floor(listed * avg_fresh / 100)` tại lúc `cook_started` | Kiểm tra payload sự kiện `cook_started` và `base_price` | `test_dynamic_pricing_based_on_freshness_and_tips` | **Đạt** |
| **AC-P3-14** | Tiền boa tính $20\%$ trên `base_price` đã chốt theo độ tươi khi phục vụ $\ge 50\%$ kiên nhẫn | Kiểm tra sự kiện `served` và tiền thanh toán `paid` | `test_dynamic_pricing_based_on_freshness_and_tips` | **Đạt** |
| **AC-P3-15** | Rơi đồ LIFO khi va chạm quái/ngất trả về mảng cá thể `{id, kind, fresh}` | Kiểm tra sự kiện `monster_hit` và `faint` với mảng cá thể LIFO | `test_gather_choke_and_faint`, `test_crocodile_chase_and_hit` | **Đạt** |
| **AC-P3-16** | Bàn giao kho cá thể nguyên vẹn qua file `--inventory-out` và trong `DaySim` | Smoke test 2 tiến trình tích hợp và vòng ngày 1-2 ngày | [catch.json](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-3/catch.json), [quan.jsonl](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-3/quan.jsonl), [day_1.jsonl](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-3/day_1.jsonl) | **Đạt** |
| **AC-P3-17** | HUD hiển thị số % tươi và nhãn cảnh báo trực quan hàng tươi/ươn trên giao diện | Kiểm tra giao diện web client tại `chonoi/web/index.html` | [index.html](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/chonoi/web/index.html) | **Đạt** |

---

## Bằng chứng kiểm thử tích hợp (Smoke Integration)

1. **Luồng gather xuất kho cá thể -> quan nạp kho cá thể:**
   - Lệnh lặn xuất kho:
     ```bash
     python -m chonoi.headless --mode gather --seed 42 --ticks 1 --scenario docs/proof/phase-3/dock_scen.json --inputs docs/proof/phase-3/dock_input.json --out docs/proof/phase-3/gather.jsonl --inventory-out docs/proof/phase-3/catch.json
     ```
     -> Exit code: `0`. File xuất: [catch.json](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-3/catch.json) có nội dung:
     `{"items":[{"id":"I1","kind":"ca_linh","fresh":99.992}]}`.
   - Lệnh mở quán nạp kho:
     ```bash
     python -m chonoi.headless --mode quan --seed 42 --inventory docs/proof/phase-3/catch.json --ticks 0 --out docs/proof/phase-3/quan.jsonl
     ```
     -> Exit code: `0`. Snapshot tick 0 trong [quan.jsonl](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-3/quan.jsonl) nhận đúng:
     `"stock":[{"id":"I1","kind":"ca_linh","fresh":99.992}]`.

2. **Luồng vòng ngày hoàn chỉnh `--mode day --days 1`:**
   - Lệnh chạy:
     ```bash
     python -m chonoi.headless --mode day --seed 42 --ticks 60 --days 1 --out docs/proof/phase-3/day_1.jsonl
     ```
     -> Exit code: `0`. File kết quả: [day_1.jsonl](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-3/day_1.jsonl).

3. **Bộ test tự động:**
   - Toàn bộ **55/55 test** (gồm 45 test P1–P2 và 10 test P3 mới) đều đạt 100% OK trong [test.log](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-3/test.log).
