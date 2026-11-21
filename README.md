# Day 12 — AI SDLC: Quán Ăn Chợ Nổi (Release v1.0.0)

> **Nhóm OngCan** · Trò chơi mô phỏng quản lý 2D "Quán Ăn Chợ Nổi Rạch Sen" (Út Sen lặn sông bắt cá, hái hoa buổi sáng và mở quán nổi buổi tối).  
> **Tác giả:** Nguyễn Mạnh Quân (GitHub: `@osgi23`, MSV: `2A202603776`) · Nhóm 1 thành viên (`team_size: 1`).  
> **Phiên bản:** `v1.0.0` (Test Contract `v1.3`).

---

## 1. Chạy nhanh từ Repo sạch (Tối đa 3 lệnh)

Chỉ dùng thư viện chuẩn của Python 3.10+ (không cần cài thêm thư viện phụ thuộc):

```bash
# 1. Clone repo và chuyển vào thư mục
git clone https://github.com/osgi23/K5-L3B-LAB-Day12-AI-SDLC-OngCan.git && cd K5-L3B-LAB-Day12-AI-SDLC-OngCan

# 2. Chạy toàn bộ 60 bài kiểm thử đơn vị và smoke test
python3 -m unittest discover -s tests -v

# 3. Khởi chạy game có giao diện web trực quan
python3 -m chonoi.live --mode day
```
*Mở địa chỉ in ra (mặc định `http://localhost:8000`) trên trình duyệt để chơi.*

---

## 2. Điều khiển trò chơi

| Phím | Hành động |
|---|---|
| **W, A, S, D** hoặc **Mũi tên** | Di chuyển (Bơi lặn ngang/sâu trong `gather`; đi lại trong `quan`) |
| **E** | Tương tác: Cập bến, hái hoa (sáng) / Nấu bếp, bưng món, phục vụ bàn (tối) |
| **Space** | Bắt cá khi lặn dưới nước (hồi chiêu 0.5s) |
| **C** | **Bật / Tắt chế độ Tương phản cao (High Contrast Mode)** |
| **1, 2** | Mua nâng cấp Bình Oxy / Áo Phao trong Shop cuối ngày |
| **O** | Đóng Shop để chuyển sang Ngày tiếp theo |
| **P** hoặc **Escape** | Tạm dừng (Pause) / Tiếp tục (Resume) |
| **R** | Chơi lại từ đầu (giữ nguyên seed) |

---

## 3. Các lệnh Headless, Benchmark, Soak & Leaderboard

- **Chạy kiểm thử toàn bộ (Unit & Smoke Tests)**:
  ```bash
  python3 -m unittest discover -s tests -v
  ```
- **Chạy mô phỏng Headless (1 ngày hoặc vòng ngày)**:
  ```bash
  python3 -m chonoi.headless --mode day --days 5 --seed 42 --ticks 60000 --out out.jsonl
  ```
- **Chạy Benchmark có render (1280×720, làm nóng 3s, đo 30s)**:
  ```bash
  python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
  ```
- **Chạy Soak Test độ bền 10 ngày (0 crash)**:
  ```bash
  python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
  ```
- **Xuất bảng xếp hạng Top 10 cục bộ**:
  ```bash
  python3 -m chonoi.headless --export-leaderboard leaderboard_export.json
  ```

---

## 4. Tính năng nổi bật & Sáng tạo của nhóm

1. **Âm thanh thực tế qua Web Audio API & Hiệu ứng hạt (Particle Effects)**:
   - Tự động tổng hợp âm thanh bằng oscillator (không cần tải file ngoài): tiếng bọt nước bì bõm, xèo xèo nấu bếp, ting món chín, keng keng nhận tiền & boa, cảnh báo cá sấu.
   - Nhạc nền đồng quê Nam Bộ 8-bit êm dịu, có nút Bật/Tắt âm thanh tiện lợi (phím `M`).
   - Hệ thống hạt sống động: bọt nước nổi khi lặn, khói bếp bốc khi nấu, chữ tiền bay `+60k`, `+12k (boa ⭐)` trên đầu bàn ăn.
   - Tạo hình Út Sen với nón lá vàng và khăn rằn Nam Bộ đặc trưng.
2. **Trợ năng, Cảnh báo & La bàn điều hướng**:
   - 3 Cảnh báo trực quan nổi bật kèm biểu tượng: Thủy quái rượt gần, Oxy sắp cạn (< 5s), Khách chờ sắp giận (< 25% kiên nhẫn).
   - **Chế độ tương phản cao (High Contrast Mode)**: Tối ưu cho người khiếm thị màu hoặc môi trường ánh sáng yếu (phím `C`).
   - **La bàn bến tàu (Dock Compass)**: Định vị khoảng cách và chỉ hướng về bến `[2, 0]`, cảnh báo đỏ khi sắp hết giờ ca sáng.
   - Bảng xếp hạng Top 10 cao thủ xem trực tiếp trên web bằng nút `🏆 Xếp Hạng`.
3. **Quản lý kho cá thể & Suy giảm độ tươi (Mùa Nước Nổi - Contract v1.2 & v1.3)**:
   - Theo dõi từng cá thể nguyên liệu `{id, kind, fresh}`.
   - Giảm độ tươi theo giây, cảnh báo ươn khi $< 30\%$, tự động đổi nguyên liệu tươi cho khách.
   - Định giá động theo độ tươi và tính tiền boa chuẩn xác.
4. **Hiệu năng & Độ ổn định cao**:
   - Benchmark đạt trên 69 FPS trung bình, 1% low trên 63 FPS, khởi động dưới 1ms.
   - Soak test 10 ngày hoàn thành chỉ trong 1.2 giây với 0 lỗi phát sinh.

---

## 5. Tài liệu & Bằng chứng nghiệm thu
- Release Notes: [docs/release-v1.0.0.md](docs/release-v1.0.0.md)
- Nhật ký thay đổi: [CHANGELOG.md](CHANGELOG.md)
- Kế hoạch Phase 4: [docs/plan/phase-4.md](docs/plan/phase-4.md)
- Nghiệm thu tiêu chí: [docs/verification/phase-4.md](docs/verification/phase-4.md)
- Bằng chứng thực nghiệm: [docs/proof/phase-4/](docs/proof/phase-4/)
- Đóng góp thành viên: [docs/members/osgi23.md](docs/members/osgi23.md)
- Giấy phép & Ghi công: [LICENSE](LICENSE) · [CREDITS.md](CREDITS.md)
