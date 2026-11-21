# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P1-01: Bơi, gia tốc ramp, chặn mép (d không âm) | Chạy unit test Movement trong test_smoke_p1.py | `docs/proof/phase-1/test.log` (test_move_*) | Đạt |
| AC-P1-02: Lặn (dive) & Nổi (surface) khi đổi phía biên d = 0.5 | Chạy test_gather_dive_and_surface_events | `docs/proof/phase-1/test.log` (test_gather_dive_and_surface_events) | Đạt |
| AC-P1-03: Tiêu hao oxy dưới nước & hồi oxy trên mặt nước | Chạy test_gather_oxygen_consumption_and_empty | `docs/proof/phase-1/test.log` (test_gather_oxygen_consumption_and_empty) | Đạt |
| AC-P1-04: Ngạt nước (choke) đủ 60 tick & ngất (faint/fainted) mất giỏ LIFO | Chạy test_gather_choke_and_faint | `docs/proof/phase-1/test.log` (test_gather_choke_and_faint) | Đạt |
| AC-P1-05: Hái cây ở mặt nước (gather, hold_full, node_regrown) | Chạy test_gather_node_interaction_and_hold_full | `docs/proof/phase-1/test.log` (test_gather_node_interaction_and_hold_full) | Đạt |
| AC-P1-06: Bắt cá dưới nước (fish_caught, yield, cooldown) | Chạy test_gather_fish_catch_and_cooldown | `docs/proof/phase-1/test.log` (test_gather_fish_catch_and_cooldown) | Đạt |
| AC-P1-07: Cập bến (docked) & xuất file kho an toàn | Chạy test_inv_01_gather_writes_inventory_quan_reads_it | `docs/proof/phase-1/test.log` (test_inv_01_*) | Đạt |
| AC-P1-08: Quán nhận kho từ file / scenario | Chạy test_inv_01_gather_writes_inventory_quan_reads_it | `docs/proof/phase-1/test.log` (test_inv_01_*) | Đạt |
| AC-P1-09: Khách đến theo lịch, giữ chỗ nguyên liệu khả dụng | Chạy unit test quan | `docs/proof/phase-1/test.log` (test_quan_*) | Đạt |
| AC-P1-10: Nấu bếp (cook_started, dish_ready), bưng (dish_picked), phục vụ (served) | Chạy test_quan_cook_pick_serve_and_pay | `docs/proof/phase-1/test.log` (test_quan_cook_pick_serve_and_pay) | Đạt |
| AC-P1-11: Thanh toán (paid), tính boa và cộng uy tín | Chạy test_quan_cook_pick_serve_and_pay | `docs/proof/phase-1/test.log` (test_quan_cook_pick_serve_and_pay) | Đạt |
| AC-P1-12: Hết kiên nhẫn bỏ về (customer_left, patience), trừ uy tín | Chạy test_quan_customer_leaves_on_patience_zero | `docs/proof/phase-1/test.log` (test_quan_customer_leaves_on_patience_zero) | Đạt |
| AC-P1-13: Hết ca đóng cửa (closing), trả tiền món đang ăn, khách chờ rời đi, kết thúc quan_end | Chạy test_quan_closing_time_payment_and_departure | `docs/proof/phase-1/test.log` (test_quan_closing_time_payment_and_departure) | Đạt |

## Đánh giá ngắn
- **Yêu cầu nào đạt / chưa đạt:** Toàn bộ 13 AC cốt lõi của Phase 1 đã hoàn thành và đạt 100% test kiểm chứng.
- **Điều cần chỉnh cho phase sau:** Sẵn sàng đón nhận Ticket Phase 2 (mở rộng sinh vật, cá bơi, thực khách mới).
