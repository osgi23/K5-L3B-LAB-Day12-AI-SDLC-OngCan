# Kế hoạch thực hiện Phase 3 — Ticket-03: Change Request “Mùa Nước Nổi”

- Thời gian: 35 phút (1:55 – 2:30)
- Test Contract: v1.2
- Hạn đẩy tag: 2:30 (`phase-3`)
- Người thực hiện: Nguyễn Mạnh Quân (osgi23)

---

## 1. Mục tiêu trọng tâm
1. Nâng cấp hợp đồng lên **Test Contract v1.2**:
   - Chuyển đổi toàn diện từ kho đếm loại sang **kho cá thể**: `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}`.
   - Thêm cấu hình `freshness` vào tuning: initial 100, gather decay 0.5/s, quan decay 0.25/s, spoiled threshold 30.
   - Từ chối file kho đếm cũ bằng mã thoát 2 (`BadInput`).
2. Quản lý vòng đời độ tươi nguyên liệu:
   - Nguyên liệu mới: `fresh = 100` lúc bắt/hái, bắt đầu hao tươi từ tick tiếp theo.
   - Tốc độ hao: Giỏ lặn giảm $0.5 / 60$ mỗi tick; kho quán giảm $0.25 / 60$ mỗi tick. Đóng băng khi pause. Không hao tươi khi đang nấu hoặc trong Shop.
   - Ngưỡng ươn: `fresh < 30`. Phát sự kiện `spoiled` một lần duy nhất khi chuyển trạng thái từ $\ge 30$ sang $< 30$. Hàng ươn không được dùng nấu.
3. Giữ chỗ theo ID & Định giá linh hoạt theo độ tươi:
   - Giữ chỗ `customers[].reserved` là mảng ID: `["I1", "I3"]`, ưu tiên chọn cá thể tươi nhất và tie-break theo ID nhỏ hơn.
   - Khi nguyên liệu giữ chỗ bị ươn: giải phóng toàn bộ nguyên liệu giữ của đơn và thử giữ lại một lần. Nếu thất bại, chuyển trạng thái đơn sang `unfulfillable`.
   - Bắt đầu nấu chốt giá theo độ tươi: `base_price = floor(listed_price * avg_fresh / 100)`. Tiền boa tính theo $20\%$ của `base_price` này.
4. Trực quan hóa HUD & Đảm bảo bộ test tự động xanh hoàn toàn (100% pass), lưu proof và gắn tag `phase-3`.

---

## 2. Phân chia 4 lát cắt kỹ thuật (Slices)

### Slice 1: Contract v1.2 & Bộ chuyển đổi Kho / Kịch bản (Phút 0 – 10)
- Cập nhật `game.contract.json` với `contract_version: "1.2"` và khối `freshness`.
- Cập nhật `chonoi/contract.py` kiểm tra tuning v1.2.
- Nâng cấp `chonoi/inventory.py`:
  - `validate_items`: Kiểm tra mảng các đối tượng `{id, kind, fresh}`. Bắt buộc từ chối dictionary đếm cũ với lỗi `BadInput` (exit code 2).
  - `read_inventory` & `write_inventory`: Đọc và ghi mảng cá thể qua file tạm nguyên tử, sắp xếp theo ID.
- Nâng cấp `chonoi/scenario.py`:
  - Kiểm tra `gather.hold` và `quan.stock` theo schema mảng cá thể.
  - Kiểm tra `customers[].reserved` là mảng ID nguyên liệu hợp lệ, chưa bị ươn và khớp công thức món.

### Slice 2: Logic Lặn & Hái (GatherSim) với Độ tươi & LIFO (Phút 10 – 18)
- Sử dụng `IdAllocator` để cấp phát ID `I1, I2, ...` liên tục cho từng nguyên liệu hái hoặc bắt được.
- Tại đầu bước: trừ độ tươi $0.5 / 60$ cho các cá thể có sẵn trong giỏ; phát hiện và phát sự kiện `spoiled` theo thứ tự ID.
- Thu hoạch cây (`interact`) và bắt cá (`catch`): gán `fresh = 100` cho từng cá thể mới.
- Rơi đồ khi va chạm quái (`monster_hit`) hoặc ngạt/ngất (`faint`): bỏ theo nguyên tắc LIFO, trả về mảng các đối tượng cá thể bị mất.
- Kết thúc ca lặn: xuất `inventory` trong `gather_end` và qua `--inventory-out` đúng chuẩn mảng cá thể (rỗng nếu ngất).

### Slice 3: Logic Quán Ăn (QuanSim) với Giữ chỗ theo ID & Giá động (Phút 18 – 26)
- Tại đầu bước: trừ độ tươi $0.25 / 60$ cho toàn bộ kho thô (kể cả hàng đang giữ chỗ).
- Phát sự kiện `spoiled` theo ID nếu có nguyên liệu chạm ngưỡng $< 30$.
- Xử lý các đơn có nguyên liệu giữ chỗ bị ươn: nhả toàn bộ phần giữ, thử cấp lại một lần theo thứ tự `order_tick` rồi ID bàn. Nếu thiếu nguyên liệu, gán `order_status = "unfulfillable"`.
- Khách mới đến: chọn món khả dụng (chỉ tính nguyên liệu $\ge 30$), giữ các cá thể tươi nhất theo ID.
- Tương tác bếp: lấy đơn giữ cũ nhất, tiêu hao đúng các ID, tính `avg_fresh`, chốt `base_price = floor(listed_price * avg_fresh / 100)`. Phát `cook_started` kèm mảng `items` cá thể sắp xếp theo kind rồi ID.
- Thanh toán và boa: tính boa trên `base_price` đã chốt theo độ tươi.

### Slice 4: Day & Shop Loop, HUD Client, Suite Kiểm Thử & Đóng Gói (Phút 26 – 35)
- Bàn giao kho cá thể giữa `gather` và `quan` trong `DaySim`. Giữ nguyên chuỗi ID qua các pha và ngày. Hủy kho dư khi sang ngày mới.
- Cập nhật HUD trong `chonoi/web/index.html` hiển thị số % tươi và nhãn cảnh báo trực quan hàng tươi/ươn.
- Soạn thảo bộ kiểm thử tự động `tests/test_phase3_rules.py` kiểm chứng toàn diện mọi yêu cầu và trường hợp biên của Ticket-03.
- Cập nhật các test cũ trong `test_smoke_p1.py` để tương thích Contract v1.2.
- Chạy toàn bộ test, ghi log kết quả vào `docs/proof/phase-3/test.log`.
- Hoàn thiện CHANGELOG, ADR, verification doc, cập nhật nhật ký AI, commit và gắn tag `phase-3`.
