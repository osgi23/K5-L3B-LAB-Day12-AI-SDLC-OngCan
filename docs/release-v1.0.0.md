# Release Notes — Quán Ăn Chợ Nổi v1.0.0

Phiên bản phát hành chính thức **v1.0.0** của trò chơi mô phỏng 2D **Quán Ăn Chợ Nổi** (Lab Day 12 · AI SDLC · VinUni K5-L3B).

---

## 1. Điểm mới nổi bật trong v1.0.0

### Trải nghiệm gameplay hoàn chỉnh
- **Vòng ngày 3 giai đoạn (DaySim)**:
  - **Sáng (Lặn & Hái)**: Út Sen bơi lặn trong lòng sông Tiền, hái bông điên điển, bông súng, kèo nèo; bắt cá linh, cá lóc, cá kèo; né tránh thủy quái Cá Sấu Năm Chèo tuần tra và rượt đuổi.
  - **Chiều tối (Mở quán nổi)**: Tiếp đón thực khách, phân bổ bếp nấu các món đặc sản miền Tây (Lẩu mắm, Cá lóc nướng trui, Canh chua cá linh bông điên điển, Gỏi bông súng...), phục vụ đúng bàn, nhận thanh toán và tiền boa.
  - **Đêm (Tiệm tạp hóa)**: Dùng tiền kiếm được mua bình oxy và áo phao nâng cấp cho ngày hôm sau.

### Hệ thống nguyên liệu & Độ tươi sống cá thể (Contract v1.2 & v1.3)
- Quản lý nguyên liệu dạng mảng cá thể (`{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}`).
- Cơ chế suy giảm độ tươi theo thời gian thực (giỏ lặn $-0.5$/s, kho quán $-0.25$/s, đóng băng khi tạm dừng).
- Cảnh báo và phát sự kiện `spoiled` khi nguyên liệu chạm ngưỡng $< 30\%$. Tự động nhả và tìm nguyên liệu tươi thay thế cho khách.
- Định giá động theo độ tươi: Giá món ăn thực tế được tính theo độ tươi trung bình của nguyên liệu đưa vào bếp, tiền boa tính dựa trên giá động này.

### Hiệu năng & Khả năng vận hành (Contract v1.3)
- **Benchmark chuẩn hóa có render (`chonoi.bench`)**:
  - Đo đạc mô phỏng đồ họa 1280x720 với 3s làm nóng và 30s đo đạc.
  - Đạt trên 70 FPS trung bình, 1% low FPS trên 65, khởi động dưới 0.1s.
- **Soak headless 10 ngày (`chonoi.soak`)**:
  - Chạy mô phỏng bền bỉ 10 ngày liên tục không lỗi, không rò rỉ bộ nhớ (`crashes = 0`).
  - Hỗ trợ bot tất định thông minh tự động hoàn thành cả 3 ca trong ngày.
- **Bảng xếp hạng cục bộ (Leaderboard)**:
  - Lưu trữ top 10 điểm cao nhất khi hoàn thành đủ 5 ngày chuẩn.
  - Xuất bảng xếp hạng chuẩn hóa với cờ `--export-leaderboard`.

### Trợ năng & Trải nghiệm người dùng
- **3 Cảnh báo trực quan**: Cảnh báo thủy quái gần / đang đuổi, Cảnh báo oxy nguy cấp (< 5s), Cảnh báo khách chờ sắp giận.
- **Chế độ tương phản cao (High Contrast Mode)**: Nhấn phím `C` hoặc nút giao diện để chuyển sang tông màu đen/vàng/cyan/đỏ sắc nét, viền dày.
- **Phụ đề SFX**: Hiện phụ đề văn bản mô tả âm thanh trực quan cho mọi hành động trong game.

---

## 2. Hướng dẫn chạy từ Repo sạch (Tối đa 3 lệnh)

Chỉ dùng thư viện chuẩn của Python 3.10+ (không cần cài đặt thư viện ngoài qua pip):

```bash
# 1. Clone repo và chuyển vào thư mục dự án
git clone https://github.com/osgi23/K5-L3B-LAB-Day12-AI-SDLC-OngCan.git && cd K5-L3B-LAB-Day12-AI-SDLC-OngCan

# 2. Chạy toàn bộ 60 bài kiểm thử đơn vị và smoke test
python3 -m unittest discover -s tests -v

# 3. Khởi chạy game có giao diện web trực quan
python3 -m chonoi.live --mode day
```
*Mở địa chỉ `http://localhost:8000` (hoặc cổng in ra) trên trình duyệt để thưởng thức trọn vẹn trò chơi.*

---

## 3. Điều khiển trò chơi
| Phím | Hành động |
|---|---|
| **W, A, S, D** hoặc **Mũi tên** | Di chuyển (Bơi lặn / Đi lại trong quán) |
| **E** | Tương tác (Hái cây, Cập bến, Nấu bếp, Nhặt món, Giao bàn) |
| **Space** | Bắt đàn cá dưới nước |
| **1, 2** | Mua nâng cấp Bình Oxy / Áo Phao trong Shop |
| **O** | Đóng Shop để chuyển sang Ngày tiếp theo |
| **C** | Bật / Tắt chế độ Tương phản cao (High Contrast Mode) |
| **P** hoặc **Escape** | Tạm dừng (Pause) / Tiếp tục (Resume) |
| **R** | Chơi lại từ đầu |

---

## 4. Các lệnh Headless, Benchmark & Soak
- **Chạy mô phỏng headless**:
  ```bash
  python3 -m chonoi.headless --mode day --days 5 --seed 42 --ticks 60000 --out out.jsonl
  ```
- **Chạy benchmark hiệu năng**:
  ```bash
  python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
  ```
- **Chạy soak test 10 ngày**:
  ```bash
  python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
  ```
- **Xuất bảng xếp hạng**:
  ```bash
  python3 -m chonoi.headless --export-leaderboard leaderboard_export.json
  ```

---

## 5. Giới hạn đã biết (Known Limitations)
- Trò chơi sử dụng canvas web 2D đơn giản qua HTTP polling tiêu chuẩn để đảm bảo chạy mượt trên mọi hệ điều hành không cần cài đặt thêm dependency.
- Âm thanh SFX hiện tại được hiển thị qua hệ thống phụ đề chữ nổi bật (visual SFX subtitle) thay vì phát audio qua loa.
