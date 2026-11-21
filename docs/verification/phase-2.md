# Ma trận truy vết Phase 2 (Ticket-02 — Test Contract v1.1)

| AC | Cách kiểm chứng | Bằng chứng (link file proof) | Kết quả |
|---|---|---|---|
| AC-P2-01: Contract v1.1, tuning chuẩn, 6 nguyên liệu | Kiểm tra `game.contract.json`, test schema kho | `docs/proof/phase-2/test.log` (test_con_*, test_inv_*) | Đạt |
| AC-P2-02: 6 nút hái N1–N6, mọc lại 20s, bến trước hái | Chạy unit test gather node interaction | `docs/proof/phase-2/test.log` (test_gather_node_*) | Đạt |
| AC-P2-03: Bắt 3 loài cá (linh: 3, lóc: 1, kèo: 2), hồi 0.5s | Chạy unit test catch & yield cá linh, lóc, kèo | `docs/proof/phase-2/test.log` (test_gather_fish_*) | Đạt |
| AC-P2-04: Đàn cá bơi 1.5 m/s, đổi hướng mỗi 120 tick, phản xạ mép | Chạy kịch bản v1.1 full cá bơi trong test_phase2_rules | `docs/proof/phase-2/test.log` (test_v11_full_fish_and_monsters) | Đạt |
| AC-P2-05: Sinh cá đầu ca 8 đàn, sinh thêm tại tick 360·k (trần 12 đàn) | Chạy kiểm tra event fish_spawned tại tick 360 | `docs/proof/phase-2/test.log` (test_v11_full_fish_and_monsters) | Đạt |
| AC-P2-06: Cá Sấu Năm Chèo tuần tra, rượt, chạm hit mất 1 HP + nửa giỏ LIFO + bất tử 90 tick + recoil 60 tick | Chạy test crocodile chase and hit trong test_phase2_rules | `docs/proof/phase-2/test.log` (test_crocodile_chase_and_hit) | Đạt |
| AC-P2-07: Quán 2 bếp B1–B2, 4 bàn T1–T4, 6 món ăn | Kiểm tra fixture và thực đơn menu | `docs/proof/phase-2/test.log` (test_quan_*) | Đạt |
| AC-P2-08: Khách gọi món lọc theo day_plan trong mode day | Chạy kiểm tra khách chỉ gọi món thuộc day_plan | `docs/proof/phase-2/test.log` (test_day_cycle_and_shop_upgrades) | Đạt |
| AC-P2-09: Vòng ngày hoàn chỉnh (--mode day --days N, N in [1, 5]) | Chạy headless mode day 1 ngày và 2 ngày | `docs/proof/phase-2/day_1.jsonl`, `test.log` | Đạt |
| AC-P2-10: Cửa hàng nâng cấp cuối ngày (Shop: oxy, máu, buy, shop_done) | Chạy kiểm tra event bought, shop_end trong test_phase2_rules | `docs/proof/phase-2/test.log` (test_day_cycle_and_shop_upgrades) | Đạt |
| AC-P2-11: Hiệu lực nâng cấp áp dụng từ ngày kế tiếp (active_upgrades) | Kiểm tra snapshot gather ngày 2 thấy oxy max = 2700 ticks | `docs/proof/phase-2/test.log` (test_day_cycle_and_shop_upgrades) | Đạt |
| AC-P2-12: Cơ chế Pause: bấm pause dừng tick mô phỏng, bấm tiếp resumed | Chạy kịch bản pause/resume, kiểm tra event paused/resumed | `docs/proof/phase-2/test.log` (test_pause_and_resume) | Đạt |
| AC-P2-13: Kiểm tra lỗi kịch bản v1.1 phải exit 2 trước khi ghi đầu ra | Chạy kịch bản kiểm tra lỗi tham số và scenario vi phạm | `docs/proof/phase-2/test.log` (test_scenario_v11_error_exit_2) | Đạt |

## Bằng chứng kiểm thử tích hợp (Smoke Integration)
1. **Luồng gather xuất kho -> quan nạp kho:**
   - Lệnh gather xuất kho: `python -m chonoi.headless --mode gather --seed 42 --ticks 5 --inputs docs/proof/phase-2/dock_input.json --out docs/proof/phase-2/gather.jsonl --inventory-out docs/proof/phase-2/catch.json` (exit code 0).
   - Lệnh quan nạp kho: `python -m chonoi.headless --mode quan --seed 42 --inventory docs/proof/phase-2/catch.json --ticks 10 --out docs/proof/phase-2/quan.jsonl` (exit code 0).
   - File kết quả: `docs/proof/phase-2/catch.json`, `docs/proof/phase-2/gather.jsonl`, `docs/proof/phase-2/quan.jsonl`.
2. **Luồng vòng ngày `--mode day --days 1`:**
   - Lệnh chạy: `python -m chonoi.headless --mode day --seed 42 --days 1 --ticks 100 --out docs/proof/phase-2/day_1.jsonl` (exit code 0).
   - File kết quả: `docs/proof/phase-2/day_1.jsonl`.
3. **Bộ test tự động:**
   - Toàn bộ 45 unit và integration tests đạt 100% OK trong `docs/proof/phase-2/test.log`.

## Đánh giá
- **Đạt được:** Hoàn thành 100% yêu cầu cốt lõi của Phase 2 (Test Contract v1.1), đầy đủ 13 AC.
- **Tiến độ:** Hoàn thành trước hạn tag 1:55.
