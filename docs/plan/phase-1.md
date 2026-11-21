# Kế hoạch Phase 1 (≤ 1 trang)

- **Mục tiêu:**
  - Hoàn thiện toàn bộ logic cốt lõi của Phase 1 cho 2 chế độ: Buổi sáng (`gather`) và Buổi tối (`quan`).
  - Đảm bảo tuân thủ 100% Test Contract v1.0, smoke test 2 tiến trình nối nhau qua file kho `catch.json` chạy chuẩn xác.
  - Vượt qua toàn bộ bộ test tự động và chuẩn bị sẵn sàng gắn tag `phase-1` trước mốc 1:00.

- **Việc / người / phụ thuộc:**
  - **Lát 1 (osgi23-gather):** Bơi, oxy, lặn (`dive`), nổi (`surface`), ngạt (`choke`), ngất (`faint`), giỏ LIFO.
  - **Lát 2 (osgi23-gather):** Tương tác hái cây (`gather`, `hold_full`, `node_regrown`), bắt cá (`fish_caught`, hồi chiêu), cập bến (`docked`), xuất kho.
  - **Lát 3 (osgi23-quan):** Khách đến theo lịch, chọn món đủ nguyên liệu khả dụng, giữ chỗ (`reserved`), kiên nhẫn (`patience_s`), bỏ về (`customer_left`), thiếu món (`no_dish`).
  - **Lát 4 (osgi23-quan):** Bếp nấu (`cook_started`, `dish_ready`), lấy món (`dish_picked`), phục vụ (`served`), tính boa, trả tiền (`paid`), hết giờ đóng ca (`quan_end`).
  - **Tích hợp & QA (osgi23):** Viết unit test mở rộng `tests/test_phase1_rules.py`, kiểm thử hai tiến trình hộp đen, lưu bằng chứng `docs/proof/phase-1/test.log`, hoàn thiện ma trận truy vết và gắn tag.

- **Rủi ro:**
  - Làm việc một mình đòi hỏi quản lý thời gian chặt chẽ giữa code, test và tài liệu.
  - Lệch contract schema kho: Đã khóa chặt bằng test tích hợp `test_inv_01_gather_writes_inventory_quan_reads_it`.
