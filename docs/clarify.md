# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 09:30 | Do các nhóm khác đã đủ thành viên (full), sinh viên làm solo thì xử lý danh sách TEAM.md thế nào? | Khai báo 4 slot theo vai trò/module phụ trách với handle chính là osgi23 để vượt qua kiểm tra định dạng của `tools/check_team.py` và CI. | PO (osgi23) |
| 2 | 2026-11-21 09:33 | Khi người chơi ngất (faint do ngạt), thứ tự bỏ giỏ là gì và kho xuất ra thế nào? | Thứ tự bỏ giỏ LIFO (nhặt sau bỏ trước), phát sự kiện faint chứa mảng `lost`, kho xuất ra rỗng `{"items":{}}`. | PO (osgi23) |
| 3 | 2026-11-21 09:35 | Món vừa chuyển sang ready trên bếp ở bước 2 có được tăng ready_ticks ở bước 1 của tick đó không? | Không, chỉ tăng `ready_ticks` cho món đã ready từ đầu bước theo đúng đặc tả PRD-0. Món vừa nấu xong có `ready_ticks = 0`. | PO (osgi23) |
| 4 | 2026-11-21 09:36 | Khi hết ca mà khách đang ăn thì xử lý ra sao? | Khách đang ăn được thanh toán ngay với reason `closing` (vẫn tính tiền món + boa nếu có), khách đang chờ rời đi với reason `closing` và không bị trừ uy tín. | PO (osgi23) |
