# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt:
  - Xây dựng kiến trúc `DaySim`, `ShopSim`, `GatherSim`, `QuanSim` module hóa cao, sạch sẽ và dễ kiểm thử độc lập.
  - Phân tách rõ ràng giữa `upgrades` (cấp mua trong Shop) và `active_upgrades` (cấp áp dụng trong ngày), đảm bảo nâng cấp mua chỉ có hiệu lực từ ngày kế tiếp.
  - Đạt 100% test xanh (45/45 tests), đầy đủ bằng chứng tích hợp hai tiến trình và vòng ngày đa ngày.
- Điều tệ:
  - Khác biệt cú pháp PowerShell trên Windows ($env:PYTHONPATH) đôi lúc gây lỗi nếu không chú ý môi trường chạy.
  - Xử lý cạnh lên nút Pause cần nhả phím giữa hai lần bấm để tạo cạnh lên false -> true.
- 1 hành động cho Phase 3:
  - Khi nhận Change Request (Ticket-03), thực hiện phân tích tác động (Impact Analysis) và lập ADR kỹ lưỡng trước khi chỉnh sửa logic lõi để không gây hồi quy (regression) cho vòng ngày.

## Phase 3 (nhanh)
- Điều tốt:
  - Lập ADR-0001 và bảng phân tích tác động chi tiết trước khi code giúp quá trình Breaking Change từ kho đếm sang kho cá thể (v1.2) diễn ra chuẩn xác, không làm vỡ vòng ngày `DaySim`.
  - Cấp phát ID cá thể `I1, I2, ...` liên tục, duy nhất và bảo lưu xuyên suốt các ca chơi và các ngày.
  - Xử lý mượt mà cơ chế phát hiện ươn (`spoiled`), tái giữ chỗ tự động cho đơn khách khi hàng bị ươn, và tính giá động theo độ tươi nguyên liệu.
  - Đạt 55/55 test xanh hoàn toàn (100%), đầy đủ proof tích hợp và cập nhật trực quan trên HUD client.
- Điều tệ:
  - Ban đầu độ chính xác làm tròn trong `inventory.py` (6 số) lệch so với `jsonl.py` (3 số), cần đồng bộ về chuẩn 3 chữ số thập phân (`round(v, 3)`).
- 1 hành động cho Phase 4:
  - Tối ưu hóa hiệu năng, benchmark tick rate mô phỏng, đóng gói phát hành Release v1.0.0 hoàn chỉnh và hoàn thành toàn bộ tài liệu tổng kết lab.

## Phase 4 (cuối)
- **Rà lại hành động Phase 2**: ĐÃ HOÀN THÀNH. Nhóm đã thực hiện phân tích tác động và lập [ADR-0001](adr/0001-item-based-inventory.md) chi tiết trước khi code Phase 3. Nhờ đó, việc Breaking Change sang kho cá thể và độ tươi (v1.2) không làm vỡ bất kỳ logic vòng ngày hay kịch bản nào, giữ vững 55/55 test xanh trước khi bước vào Phase 4.
- **Điều tốt**:
  - Thực thi hoàn hảo Test Contract v1.3: Cả hai lệnh `bench_cmd` và `soak_cmd` đều đạt và vượt xa chỉ tiêu đề ra (Benchmark đạt 69 FPS, 1% low 63 FPS, load 1ms; Soak hoàn thành trọn vẹn 10 ngày trong 1.2 giây với 0 crash).
  - Tích hợp 3 cảnh báo trực quan dễ nhận biết bằng chữ và biểu tượng, bổ sung chế độ tương phản cao (phím C) và hệ thống phụ đề âm thanh SFX cho client web.
  - Hoàn thiện tính năng mở rộng Bảng xếp hạng cục bộ (Leaderboard) lưu top 10 bền vững với thuật toán sắp xếp điểm ổn định (stable sort) và hỗ trợ xuất dữ liệu độc lập.
  - Bộ test hoàn chỉnh đạt 60/60 bài test pass (100%), đầy đủ bằng chứng thực nghiệm trong `docs/proof/phase-4/`.
- **Điều tệ**:
  - Khi viết bot tất định cho `soak.py`, ban đầu gọi nhầm `sim.player["pos"]` thay vì `sim.pos` của `QuanSim`, gây lỗi crash ở lần thử đầu. Tuy nhiên đã phát hiện và khắc phục ngay trong vài phút nhờ chạy thử nghiệm lệnh.
- **Số liệu dự án**:
  - Số commit: 7 commit hoàn chỉnh, gắn tag chuẩn `phase-1`, `phase-2`, `phase-3`, `phase-4`, và `v1.0.0`.
  - Token ước tính: ~140.000 input tokens, ~35.000 output tokens.
  - Thành viên: Nguyễn Mạnh Quân (osgi23) solo developer kiêm nhiệm đầy đủ vai trò PO, Dev, QA, Integrator.
- **Một lần AI sai và cách nhóm phát hiện**:
  - *Lỗi AI*: Khi viết bot trong `chonoi/soak.py`, AI suy luận nhầm rằng `QuanSim` có thuộc tính `sim.player["pos"]` giống như cấu trúc snapshot, trong khi thực tế `QuanSim` lưu trực tiếp tại `self.pos`.
  - *Cách phát hiện*: Nhóm chạy smoke test lệnh `python -m chonoi.soak --seed 7 --days 1 --out test_soak.json`, phát hiện thông báo lỗi trong output JSON `"crashes": 1` và traceback `'QuanSim' object has no attribute 'player'`. Nhóm đã đọc mã nguồn [chonoi/sim/quan.py](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/chonoi/sim/quan.py) để chỉnh sửa lại chính xác `px, pz = sim.pos`.
- **Nếu làm lại, đổi gì**:
  - Thống nhất quy ước đặt tên thuộc tính nội bộ giữa các lớp con `GatherSim` và `QuanSim` (hoặc tạo một interface `SimAgent` chung) để việc viết bot tự hành và bộ benchmark không bị phụ thuộc vào tên biến riêng của từng sim.
