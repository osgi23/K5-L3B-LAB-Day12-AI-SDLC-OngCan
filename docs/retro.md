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
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
