---
name: run-smoke-test
description: Chạy bộ kiểm thử tự động hộp đen và kiểm tra tính toàn vẹn của game simulation.
---

# Skill: run-smoke-test

## Khi nào dùng:
- Trước mỗi lần commit code hoặc gắn tag phase (`phase-1` ... `phase-4`).
- Khi tích hợp các thay đổi giữa module `sim/gather` và `sim/quan`.

## Cách thực hiện:
1. Chạy toàn bộ test suite:
   ```bash
   PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
   ```
2. Chạy smoke test 2 tiến trình tích hợp (PRD mục G):
   - Chạy `gather` xuất `catch.json`:
     ```bash
     python3 -m chonoi.headless --mode gather --seed 42 --ticks 1 --out gather.jsonl --inventory-out catch.json
     ```
   - Chạy `quan` nạp `catch.json`:
     ```bash
     python3 -m chonoi.headless --mode quan --seed 42 --inventory catch.json --ticks 0 --out quan.jsonl
     ```
3. Đảm bảo mã thoát là 0 và không có ngoại lệ.
