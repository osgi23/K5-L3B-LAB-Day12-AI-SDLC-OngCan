# Nguyễn Mạnh Quân (2A202603776 / osgi23) — phản tư cá nhân (≤ 200 từ)

- **Họ và tên:** Nguyễn Mạnh Quân
- **Mã sinh viên:** 2A202603776
- **GitHub handle:** osgi23

- **Tôi đã làm (kèm link commit):**
  - Đóng vai trò Solo developer kiêm PO, Integrator và QA Lead do các nhóm khác đã full.
  - Phase 1: Hoàn thiện logic Buổi sáng (`gather.py`) và Buổi tối (`quan.py`), viết `test_phase1_rules.py`, đạt 40/40 tests.
  - Phase 2: Cập nhật Test Contract v1.1, chuẩn hóa tuning; bổ sung cơ chế đàn cá bơi đổi hướng, phản xạ mép và sinh đàn cá theo lịch; triển khai quái vật Cá Sấu Năm Chèo (M1, M2) với cơ chế tuần tra, rượt đuổi, va chạm hit trừ máu, mất nửa giỏ LIFO, bất tử 90 tick và recoil 60 tick.
  - Phase 2: Triển khai Quán ăn 2 bếp (B1, B2), 4 bàn (T1–T4), thực đơn 6 món chuẩn, lọc món theo kế hoạch ngày (`day_plan`).
  - Phase 2: Triển khai vòng ngày hoàn chỉnh (`chonoi/sim/day.py`), Cửa hàng nâng cấp cuối ngày (`chonoi/sim/shop.py`), cơ chế Pause/Resume trong `chonoi/runner.py`, CLI `--days` trong `chonoi/headless.py`.
  - Phase 2: Bổ sung bộ kiểm thử `tests/test_phase2_rules.py`, đạt 45/45 tests xanh 100%.
  - Phase 3: Soạn thảo ADR-0001 và bảng phân tích tác động cho Breaking Change kho cá thể theo Change Request Ticket-03.
  - Phase 3: Nâng cấp Test Contract v1.2, cập nhật `chonoi/contract.py`, `chonoi/inventory.py` và `chonoi/scenario.py` để xử lý mảng cá thể `{id, kind, fresh}` và từ chối kho đếm cũ bằng mã thoát 2.
  - Phase 3: Triển khai hao tươi giỏ lặn 0.5/s, phát hiện ươn `spoiled`, cấp ID tuần tự `I1, I2, ...`, cơ chế rơi đồ LIFO cá thể trong `gather.py`.
  - Phase 3: Triển khai hao tươi kho quán 0.25/s, cơ chế giữ chỗ theo ID, tự động tái giữ chỗ khi hàng bị ươn, định giá động `floor(listed * avg_fresh / 100)` và tính boa theo giá mới trong `quan.py`.
  - Phase 3: Bàn giao kho cá thể trong `DaySim` và Shop, cập nhật HUD hiển thị độ tươi và nhãn ươn trong `index.html`.
  - Phase 3: Bổ sung bộ kiểm thử `tests/test_phase3_rules.py`, đạt 55/55 tests xanh 100%.
- **Tôi đã review (kèm link):**
  - Tự review toàn bộ diff trên nhánh `main` trước khi commit và gắn tag cho từng phase.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - Ở Phase 1: Subprocess test gọi `python3` thất bại trên Windows; đã shim an toàn.
  - Ở Phase 2: AI cần xử lý kỹ việc đóng Shop: vỏ event `shop_end` phải mang số ngày vừa kết thúc trước khi tăng `self.day` sang ngày mới, và cơ chế Pause cần nhả phím giữa hai lần bấm để phát hiện cạnh lên.
  - Ở Phase 3: AI ban đầu để độ chính xác làm tròn trong `inventory.py` lệch so với 3 chữ số của `jsonl.py`, dẫn đến assert so sánh kho lệch vài phần nghìn; đã đồng bộ về chuẩn 3 chữ số thập phân (`round(v, 3)`).
- **Điều tôi học được:**
  - Nắm vững quy trình xử lý Breaking Change trong phần mềm qua ADR, cách thiết kế schema mở rộng có tính tương thích ngược, quản lý trạng thái cá thể (entity-based) thay vì đếm tổng, và kỹ thuật định giá động trong game simulation.
