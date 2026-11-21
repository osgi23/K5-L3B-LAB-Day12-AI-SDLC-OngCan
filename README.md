# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Nhóm OngCan** · Dự án game 2D quản lý quán ăn Chợ Nổi Rạch Sen (Út Sen lặn sông bắt cá, hái hoa buổi sáng và mở quán nấu ăn buổi tối).
> **Lab Board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)**.

## Hướng dẫn chạy nhanh (Clone sạch trong 3 lệnh)

```bash
git clone https://github.com/osgi23/K5-L3B-LAB-Day12-AI-SDLC-OngCan.git && cd K5-L3B-LAB-Day12-AI-SDLC-OngCan
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
python3 -m chonoi.live --mode gather
```

## Chế độ Headless & Test Contract

Game hỗ trợ đầy đủ **Test Contract v1.1** độc lập GPU/UI, chạy ở 60 tick/s:
- **Chạy headless gather:**
  ```bash
  python3 -m chonoi.headless --mode gather --seed 42 --ticks 600 --out gather.jsonl --inventory-out catch.json
  ```
- **Chạy headless quan nạp kho:**
  ```bash
  python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 600 --out quan.jsonl
  ```
- **Chạy headless vòng ngày hoàn chỉnh (`day`):**
  ```bash
  python3 -m chonoi.headless --mode day --seed 42 --days 2 --ticks 1200 --out day.jsonl
  ```

## Điều khiển
- **WASD / Phím mũi tên:** Di chuyển bơi (gather: ngang và sâu [x, d]) / đi lại trong nhà bè (quan: [x, z]).
- **E (`interact`):** 
  - Buổi sáng: Cập bến (trong bến) hoặc hái hoa (ở mặt nước).
  - Buổi tối: Nấu món tại bếp / Nhặt món đã chín lên tay / Phục vụ món cho khách tại bàn.
- **Space (`catch`):** Bắt cá khi lặn dưới nước (có hồi chiêu 0.5s).
- **P / Esc (`pause`):** Tạm dừng mô phỏng (bấm lần 1 phát `paused`, bấm lần 2 phát `resumed`).
- **O (`shop_done`):** Đóng cửa hàng Shop cuối ngày.
- **R:** Chơi lại.

## Cách tính điểm (Score)
- Điểm được tính tự động tại mỗi snapshot và dòng `end`:
  $$\text{Score} = \text{Earned} + 100 \times \lfloor \text{Reputation} \rfloor$$
- Trong đó:
  - `Earned`: Tổng tiền thu được từ các món ăn đã phục vụ (gồm cả tiền boa).
  - `Reputation`: Điểm uy tín của quán (khởi đầu 3.0, tối đa 5.0, tối thiểu 0.0; phục vụ nhanh được boa + uy tín, để khách chờ hết kiên nhẫn bị trừ uy tín).

## Kiểm thử tự động (1 lệnh)

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```
Toàn bộ 45 unit test và smoke test kiểm chứng tất cả các AC của Phase 1 và Phase 2 đều vượt qua 100%.

## Sáng tạo của nhóm
- **Tách lát cắt độc lập:** Thiết kế cấu trúc xử lý trạng thái theo từng lát (Oxy/Ngạt, Hái/Bắt cá, Khách/Giữ chỗ, Bếp/Phục vụ/Thanh toán) giúp code sạch và dễ bảo trì.
- **Hệ thống cảnh báo ngạt và bảo vệ giỏ đồ:** Phản hồi mượt mà giữa trạng thái lặn và nổi, tính toán LIFO khi ngất chính xác theo Test Contract.
- **Bằng chứng lõi vẫn đúng:** Chạy toàn bộ 40 test hộp đen trong `tests/` với kết quả 40/40 OK; khớp từng byte với yêu cầu Test Contract v1.0 và PRD-0.

## Thành viên nhóm
- **Nguyễn Mạnh Quân** (MSV: `2A202603776`, GitHub: `osgi23`): Solo developer kiêm nhiệm PO, Integrator, QA Lead, Release do các nhóm trong lớp đã đủ thành viên (chi tiết tại [TEAM.md](TEAM.md) và [docs/clarify.md](docs/clarify.md)).
