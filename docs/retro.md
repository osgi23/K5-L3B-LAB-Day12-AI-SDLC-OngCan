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

## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:
