# Kế hoạch thực hiện Phase 4 — Phát hành v1.0.0

## 1. Mục tiêu
- **Phiên bản hợp đồng:** Test Contract v1.3 (`game.contract.json`, `chonoi/__init__.py`).
- **Lệnh cốt lõi:**
  - `bench_cmd`: `<bench_cmd> --seed 42 --duration 30 --out bench.json` (benchmark có render 1280x720, làm nóng 3s, đo 30s, xuất đủ 5 trường JSON).
  - `soak_cmd`: `<soak_cmd> --seed 7 --days 10 --out soak.json` (soak headless 10 Ngày, D1-D5 lặp ở D6-D10, xuất đúng schema kết quả).
- **Trải nghiệm người chơi:**
  - 3 cảnh báo trực quan dễ nhận biết: Thủy quái gần, Oxy sắp hết (< 5s), Khách sắp giận (< 25% kiên nhẫn).
  - Chế độ tương phản cao (High Contrast Mode) bật/tắt bằng phím `C` hoặc nút giao diện.
  - Phụ đề SFX cho các hiệu ứng âm thanh hành động.
- **Mở rộng:**
  - Bảng xếp hạng cục bộ (Leaderboard) lưu top 10 bền vững, xuất qua `--export-leaderboard`, ghi điểm khi hoàn thành 5 ngày chuẩn.
- **Đóng gói & Tài liệu:**
  - Hướng dẫn clone sạch trong tối đa 3 lệnh trong `README.md`.
  - Bản đóng gói zip trong `dist/`.
  - Báo cáo nghiệm thu `docs/verification/phase-4.md`, bằng chứng `docs/proof/phase-4/`.
  - Release notes, CHANGELOG, retro, clarify, ai-usage-log, standup, members/osgi23.md.
  - Gắn tag `phase-4` và `v1.0.0` đẩy lên nhánh `main`.

## 2. Phân rã công việc (Slices)
- **Slice 1: Contract v1.3 & DaySim 10 ngày**
  - Khai báo `contract_version: "1.3"`, `bench_cmd`, `soak_cmd`, `extensions: ["leaderboard"]` trong `game.contract.json`.
  - Sửa `chonoi/sim/day.py` để lặp kế hoạch D1-D5 cho D6-D10.
  - Cho phép `--days` lên đến 10 trong `chonoi/headless.py`.
- **Slice 2: Benchmark có render (`chonoi/bench.py`)**
  - Thực thi bộ đo render 1280x720, 3s làm nóng, đo `duration` giây.
  - Tính chuẩn 5 trường: `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`.
- **Slice 3: Soak headless 10 ngày (`chonoi/soak.py`)**
  - Chạy chu kỳ ngày tự động với bot tất định hoặc script input.
  - Báo cáo `days`, `days_completed`, `crashes`, `results`, `duration_s`.
- **Slice 4: Bảng xếp hạng cục bộ (`chonoi/leaderboard.py`)**
  - Lưu top 10 có sắp xếp ổn định, cờ `--leaderboard`, `--player-name`, `--export-leaderboard`.
- **Slice 5: Giao diện cảnh báo, tương phản cao & phụ đề SFX (`chonoi/web/index.html`)**
  - Vẽ quái vật, 3 cảnh báo chữ + biểu tượng nổi bật, chế độ high-contrast (phím C), phụ đề SFX.
- **Slice 6: Kiểm thử, Bằng chứng, Đóng gói & Phát hành**
  - Viết bộ test `tests/test_phase4_rules.py`.
  - Chạy regression toàn bộ 60+ test.
  - Sinh bằng chứng `docs/proof/phase-4/`.
  - Cập nhật tài liệu, đóng gói zip, commit, gắn tag `phase-4` và `v1.0.0`, push remote.
