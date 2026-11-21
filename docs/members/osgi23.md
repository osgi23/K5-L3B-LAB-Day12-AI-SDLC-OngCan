# osgi23 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Đóng vai trò Solo developer kiêm PO, Integrator và QA Lead do các nhóm khác đã full.
  - Hoàn thiện toàn bộ logic Buổi sáng (`chonoi/sim/gather.py`: oxy, lặn, nổi, ngạt, ngất, giỏ LIFO, hái cây, bắt cá, cập bến).
  - Hoàn thiện toàn bộ logic Buổi tối (`chonoi/sim/quan.py`: khách đến, giữ chỗ nguyên liệu khả dụng, nấu bếp, giao món, boa, thanh toán, kiên nhẫn, đóng ca).
  - Bổ sung bộ test `tests/test_phase1_rules.py`, đưa tổng số test lên 40/40 test xanh.
- **Tôi đã review (kèm link):**
  - Tự review toàn bộ diff trên nhánh `main` trước khi commit và gắn tag.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI ban đầu không chú ý việc gọi `python3` trong `subprocess.run` trên Windows sẽ gây lỗi `FileNotFoundError` do Windows không có sẵn executable `python3.exe`. Tôi đã phát hiện qua test log và tạo alias/copy shim `python3.exe`.
  - AI phát hiện bài test `test_template_is_rejected` trong `test_team_check.py` đọc nhầm file thật thay vì fixture template.
- **Điều tôi học được:**
  - Hiểu sâu về kiến trúc tick-based deterministic simulation (60 Hz) và cách dùng Test Contract để cô lập các module độc lập.
