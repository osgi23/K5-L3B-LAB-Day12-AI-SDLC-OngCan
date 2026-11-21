# ADR-0001: Chuyển đổi từ kho đếm loại sang kho cá thể và quản lý độ tươi nguyên liệu

- Trạng thái: Chấp nhận
- Ngày: 2026-11-21
- Người quyết: Nguyễn Mạnh Quân (osgi23)

## Bối cảnh
Theo Change Request Ticket-03 ("Mùa Nước Nổi"), vào mùa lũ, nhiệt độ cao làm nguyên liệu dễ bị ươn. Khách hàng yêu cầu theo dõi độ tươi (`fresh` trong đoạn [0, 100]) của từng cá thể nguyên liệu từ lúc Út Sen hái/bắt ở ca sáng (`gather`) cho đến khi mang về bảo quản và chế biến tại bếp (`quan`).

Schema kho cũ ở v1.0 và v1.1 chỉ đếm số lượng theo loại nguyên liệu:
```json
{"items": {"ca_loc": 2, "ca_linh": 3}}
```
Schema này không thể phản ánh độ tươi riêng biệt, thời điểm thu hoạch, thứ tự vào giỏ (LIFO), cũng như không thể định danh cụ thể cá thể nào được giữ chỗ hay sử dụng khi nấu.

## Các lựa chọn đã cân nhắc
1. **Lựa chọn 1: Lưu độ tươi trung bình theo loại nguyên liệu**
   - *Ưu điểm*: Giữ nguyên cấu trúc kho dạng dictionary đếm.
   - *Nhược điểm*: Vi phạm yêu cầu khách hàng; không xác định được cá thể cụ thể nào bị ươn (< 30), không hỗ trợ LIFO chính xác cho từng cá thể, không tuân thủ Test Contract v1.2.
2. **Lựa chọn 2: Chuyển hoàn toàn sang kho cá thể (Item-based Inventory)**
   - Cấu trúc: `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, {"id": "I2", "kind": "ca_loc", "fresh": 97.5}]}`
   - *Ưu điểm*: Đáp ứng trọn vẹn yêu cầu theo dõi cá thể, hỗ trợ cấp ID tăng dần (`I1, I2, ...`), cơ chế LIFO rơi đồ, phát hiện ươn (`spoiled`), giữ chỗ theo ID (`customers[].reserved = ["I1", "I3"]`), và định giá món ăn theo độ tươi thực tế của nguyên liệu.
   - *Nhược điểm*: Breaking change đối với schema giao tiếp giữa hai ca và các file kịch bản cũ.

## Quyết định
Nhóm quyết định thực hiện Breaking Change theo **Lựa chọn 2**, nâng cấp `contract_version` lên `"1.2"`:
1. File kho và trạng thái `hold`/`stock` lưu mảng cá thể `{id, kind, fresh}`.
2. Cấp ID tuần tự `I1, I2, ...` qua `IdAllocator`, tăng dần xuyên suốt các pha và ngày chơi.
3. Khi đọc file kho ở Contract v1.2, nếu nhận file đếm loại cũ hoặc sai schema/loại lạ/ID trùng/độ tươi ngoài [0, 100], hệ thống lập tức từ chối với mã thoát 2 (`BadInput`).
4. Độ tươi giảm 0.5/s ở giỏ lặn, 0.25/s ở kho quán; đóng băng khi pause; dừng giảm khi món bắt đầu nấu.
5. Ngưỡng ươn là `fresh < 30`. Khi cá thể chạm ngưỡng, phát event `spoiled` một lần duy nhất. Hàng ươn không được dùng để nấu.
6. Giữ chỗ chuyển sang danh sách ID: `customers[].reserved = ["I1", ...]`. Nếu nguyên liệu giữ bị ươn, hủy giữ chỗ và thử giữ lại một lần; nếu không đủ thì đánh dấu `unfulfillable`.
7. Giá món chốt tại thời điểm bắt đầu nấu theo công thức: `floor(listed_price * avg_fresh / 100)`.

## Hệ quả & Bảng phân tích tác động

| Module | File cần đổi | Thay đổi chính | Test bị ảnh hưởng | Người phụ trách |
|---|---|---|---|---|
| **Contract** | `game.contract.json`, `chonoi/contract.py`, `chonoi/__init__.py` | Nâng cấp `contract_version: "1.2"`, thêm cấu hình `tuning.freshness`. Kiểm tra tính hợp lệ của tuning mới. | `test_smoke_p1.py`, `test_phase3_rules.py` | Nguyễn Mạnh Quân |
| **Inventory Adapter** | `chonoi/inventory.py` | Cập nhật hàm `read_inventory`, `write_inventory`, `hold_to_items`. Từ chối kho đếm cũ bằng mã lỗi 2. | `test_smoke_p1.py`, `test_phase3_rules.py` | Nguyễn Mạnh Quân |
| **Scenario Validator** | `chonoi/scenario.py` | Xác thực `gather.hold`, `quan.stock` theo dạng mảng cá thể. Kiểm tra `customers[].reserved` là mảng ID hợp lệ và chưa ươn. | `test_smoke_p1.py`, `test_phase3_rules.py` | Nguyễn Mạnh Quân |
| **Lặn & Hái (Gather)** | `chonoi/sim/gather.py` | Cấp ID `I...` cho từng nguyên liệu. Trừ độ tươi 0.5/s đầu tick. Phát event `spoiled`. LIFO trả về mảng cá thể khi hit/ngất. | `test_phase1_rules.py`, `test_phase3_rules.py` | Nguyễn Mạnh Quân |
| **Quán Ăn (Quan)** | `chonoi/sim/quan.py` | Trừ độ tươi kho thô 0.25/s. Xử lý giữ chỗ theo ID. Tái giữ chỗ khi hàng giữ bị ươn. Tính `base_price` theo fresh trung bình. | `test_phase1_rules.py`, `test_phase3_rules.py` | Nguyễn Mạnh Quân |
| **Day & Shop Loop** | `chonoi/sim/day.py`, `chonoi/sim/shop.py` | Chuyển giao kho cá thể giữa gather và quan. Bảo lưu ID xuyên ngày. Hủy kho dư thừa khi sang ngày mới. | `test_phase2_rules.py`, `test_phase3_rules.py` | Nguyễn Mạnh Quân |
| **HUD / Web Client** | `chonoi/web/index.html` | Hiển thị độ tươi theo % và nhãn cảnh báo trực quan hàng tươi/ươn trên giao diện. | Kiểm thử thủ công qua live server | Nguyễn Mạnh Quân |
