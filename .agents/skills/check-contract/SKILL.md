---
name: check-contract
description: Kiểm tra hợp đồng tích hợp game.contract.json và tính tương thích của danh sách thành viên TEAM.md.
---

# Skill: check-contract

## Khi nào dùng:
- Khi khởi tạo phase mới hoặc có yêu cầu thay đổi (Change Request) tác động đến contract.
- Kiểm tra trước khi build trong CI.

## Cách thực hiện:
1. Kiểm tra danh sách thành viên:
   ```bash
   python3 tools/check_team.py
   ```
2. Xác thực tính hợp lệ của `game.contract.json` qua CLI headless:
   ```bash
   python3 -m chonoi.headless --mode gather --seed 1 --ticks 0 --out test.jsonl
   ```
3. Xóa file đầu ra tạm `test.jsonl`.
