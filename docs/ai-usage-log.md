# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| Phase 1 | Nguyễn Mạnh Quân | Antigravity (Gemini 3.8 Flash) | Khảo sát toàn bộ repo, phân tích PRD-0 và Test Contract v1.0 | ~25,000 tokens | Ban đầu subprocess test gọi `python3` thất bại trên Windows do thiếu python3.exe; đã shim thành công. |
| Phase 1 | Nguyễn Mạnh Quân | Antigravity (Gemini 3.8 Flash) | Lập trình sim/gather.py (Lát 1: oxy, ngạt, ngất; Lát 2: hái, bắt cá, cập bến) | ~18,000 tokens | AI cần lưu ý thứ tự phát event: faint phải trước gather_end(fainted), giỏ mất theo LIFO. |
| Phase 1 | Nguyễn Mạnh Quân | Antigravity (Gemini 3.8 Flash) | Lập trình sim/quan.py (Lát 3: khách, giữ chỗ; Lát 4: bếp nấu, bưng bê, thanh toán, closing) | ~22,000 tokens | AI cần chú ý chỉ tăng ready_ticks cho món đã ready từ đầu bước, không tăng ngay trong bước nấu xong. |
| Phase 1 | Nguyễn Mạnh Quân | Antigravity (Gemini 3.8 Flash) | Viết test/test_phase1_rules.py và tài liệu hóa nghiệm thu | ~15,000 tokens | AI phát hiện test_template_is_rejected đọc trực tiếp TEAM.md của nhóm thay vì chuỗi template mẫu. |
| Phase 2 | Nguyễn Mạnh Quân | Antigravity (Gemini 3.8 Flash) | Phân tích Ticket-02, cập nhật game.contract.json lên v1.1, KINDS_P2 | ~15,000 tokens | Nút attack là hợp lệ ở v1.1; cần cập nhật các test smoke cũ kiểm tra attack như nút lạ. |
| Phase 2 | Nguyễn Mạnh Quân | Antigravity (Gemini 3.8 Flash) | Lập trình đàn cá bơi/sinh, Cá Sấu Năm Chèo patrol/chase/hit/recoil trong gather.py | ~20,000 tokens | AI ban đầu chưa chặn mép độ sâu cho cá sấu khi bơi đuổi; đã kẹp d trong [10, 30]. |
| Phase 2 | Nguyễn Mạnh Quân | Antigravity (Gemini 3.8 Flash) | Lập trình Quán 2 bếp, 4 bàn, lọc menu theo day_plan, Shop nâng cấp shop.py | ~22,000 tokens | Nâng cấp Shop phải tách biệt `upgrades` và `active_upgrades` để chỉ có hiệu lực từ ngày kế tiếp. |
| Phase 2 | Nguyễn Mạnh Quân | Antigravity (Gemini 3.8 Flash) | Lập trình DaySim (day.py), Pause/Resume trong runner.py, test_phase2_rules.py | ~25,000 tokens | Vỏ event khi đóng Shop phải mang day của ngày vừa kết thúc trước khi tăng day sang ngày mới. |
