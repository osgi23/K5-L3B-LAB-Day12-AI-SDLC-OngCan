# Phản tư cá nhân — Nguyễn Mạnh Quân (osgi23)

- **Sinh viên:** Nguyễn Mạnh Quân · MSV: `2A202603776` · Nhóm OngCan (solo, `team_size: 1`).
- **Phần tôi làm:**
  - Hoàn thiện trọn vẹn 4 phase của dự án, nâng cấp qua các phiên bản Test Contract v1.0 $\to$ v1.1 $\to$ v1.2 $\to$ v1.3.
  - Phase 1 & 2: Mô phỏng lặn hái, quán ăn, cá bơi, Cá Sấu Năm Chèo, vòng ngày đa ca (`DaySim`), tiệm nâng cấp (`ShopSim`).
  - Phase 3: Lập [ADR-0001](../adr/0001-item-based-inventory.md), chuyển đổi kho cá thể, tính hao tươi, phát hiện `spoiled`, đổi nguyên liệu và định giá động.
  - Phase 4: Xây dựng bộ đo hiệu năng có render [bench.py](../../chonoi/bench.py), bộ thử độ bền 10 ngày [soak.py](../../chonoi/soak.py), bảng xếp hạng [leaderboard.py](../../chonoi/leaderboard.py), 3 cảnh báo trực quan & chế độ tương phản cao trong [index.html](../../chonoi/web/index.html).
  - Viết 60 bài kiểm thử đơn vị & smoke test ([test.log](../proof/phase-4/test.log), 100% đạt).
- **Hỗ trợ / Đóng góp:** Chia sẻ giải pháp shim môi trường PowerShell Windows cho các bạn trong lớp; tự rà soát nghiêm ngặt từng diff trước khi commit.
- **AI sai ở đâu & cách phát hiện:** Trong Phase 4, AI gọi nhầm `sim.player["pos"]` trong `QuanSim`. Tôi chạy smoke test `python -m chonoi.soak`, phát hiện traceback và sửa thành `sim.pos`.
- **Bài học:** Kỹ năng phân tích tác động khi đổi hợp đồng (Breaking Change), quản lý chu kỳ phần mềm bằng AI một cách kỷ luật và kỹ thuật tối ưu hóa hiệu năng render/headless.
