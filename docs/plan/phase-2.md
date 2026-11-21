# Kế hoạch Phase 2 (Ticket-02 — Một ngày ở chợ nổi)

- **Mục tiêu:**
  - Nâng cấp lên **Test Contract v1.1**, áp dụng bộ số liệu chuẩn (Standard Tuning).
  - Hoàn thiện mô phỏng **Buổi sáng (`gather`)**: 6 nút hái N1–N6, 3 loài cá với cơ chế bơi (1.5 m/s, đổi hướng mỗi 120 tick, phản xạ mép) và sinh cá theo lịch (phase_tick = 360·k, trần 12 đàn), quái vật Cá Sấu Năm Chèo (M1 từ ngày 1, M2 từ ngày 3, tuần tra 1.0 m/s, rượt 3.0 m/s, va chạm hit mất 1 HP + nửa giỏ LIFO + bất tử 90 tick + giật lùi recoil 60 tick).
  - Hoàn thiện **Buổi tối (`quan`)**: 2 bếp B1–B2, 4 bàn T1–T4, thực đơn 6 món chuẩn, lọc thực đơn theo kế hoạch ngày (`day_plan`).
  - Hoàn thiện **Vòng ngày hoàn chỉnh (`--mode day --days N`)**: chu kỳ ngày (day_start -> day_plan -> gather -> quan -> shop -> ngày kế hoặc kết thúc), cửa hàng nâng cấp cuối ngày (`shop`: oxy và máu), cơ chế tạm dừng (`pause` / `resume`).
  - Đảm bảo 100% test xanh (45/45 test), hoàn thành bằng chứng tích hợp và gắn tag `phase-2` đúng hạn 1:55.

- **Phân chia lát cắt & phân công (Solo `osgi23`):**
  - **Lát 1 (Số chuẩn & Cá bơi/sinh, Cá Sấu Năm Chèo):**
    - Cập nhật `game.contract.json` lên v1.1, schema kho `KINDS_P2` (6 nguyên liệu).
    - Triển khai logic bơi đổi hướng, phản xạ mép, sinh đàn cá tại `phase_tick = 360·k`.
    - Triển khai Cá Sấu Năm Chèo: tuần tra waypoint, phát hiện người chơi ở $d \ge 10$ trong $\le 10$m, rượt đuổi, va chạm hit, trừ 1 HP, mất $\lfloor \text{hold}/2 \rfloor$ LIFO, recoil 60 tick.
  - **Lát 2 (Quán ăn 2 bếp / 4 bàn & Thực đơn 6 món):**
    - 2 bếp B1, B2; 4 bàn T1–T4.
    - 6 món ăn theo công thức Ticket-02.
    - Tích hợp lọc món khách gọi theo kế hoạch ngày `day_plan` trong chế độ `day`.
  - **Lát 3 (Vòng ngày `day`, Cửa hàng `shop` & Cơ chế Pause):**
    - Module `chonoi/sim/shop.py`: xử lý lệnh mua `buy: "oxygen"|"hp"`, kiểm tra tiền, cấp nâng cấp tối đa, `shop_done`, timeout 600 tick.
    - Module `chonoi/sim/day.py`: quản lý chu trình các pha, chuyển giao kho từ gather sang quan, chuyển tiền và nâng cấp sang ngày hôm sau.
    - Cơ chế `pause` / `resumed` trong `chonoi/runner.py`.
    - Bổ sung `--days` (1 đến 5) vào `chonoi/headless.py`.
  - **Lát 4 (Kiểm thử, Xác minh & Bàn giao):**
    - Viết bộ test tích hợp `tests/test_phase2_rules.py` (v1.1 đầy đủ, vòng ngày + shop, kiểm tra lỗi hợp đồng, pause/resume).
    - Tạo bằng chứng tại `docs/proof/phase-2/` (`test.log`, `gather.jsonl`, `catch.json`, `quan.jsonl`, `day_1.jsonl`).
    - Cập nhật ma trận truy vết `docs/verification/phase-2.md`, nhật ký `ai-usage-log.md`, `retro.md`, `standup.md`.
    - Gắn git tag `phase-2` và đẩy lên `origin/main`.

- **Rủi ro & Biện pháp giảm thiểu:**
  - *Rủi ro:* Cơ chế Pause làm lệch nhịp sim_tick hoặc timer. -> *Giải pháp:* Tách biệt `self.tick` (tick ngoài) và `self.sim_tick` (tick mô phỏng), khi paused chỉ tăng `self.tick`.
  - *Rủi ro:* Cấp nâng cấp mua ở ngày n bị áp dụng ngay trong ngày n. -> *Giải pháp:* Tách biệt `upgrades` (cấp đã mua) và `active_upgrades` (cấp đang áp dụng), chỉ sao chép sang `active_upgrades` khi bắt đầu ngày mới $n+1$.
