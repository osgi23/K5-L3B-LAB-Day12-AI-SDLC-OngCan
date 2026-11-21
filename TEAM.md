# TEAM

**Tên nhóm:** OngCan  **Số người:** 4  (khớp `team_size` trong `game.contract.json`)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| osgi23 (Chính) | osgi23 | sim/gather | PO / Integrator / Release | quan |
| osgi23 (Gather) | osgi23-gather | sim/gather | Dev Lát 1 & 2 | gather |
| osgi23 (Quan) | osgi23-quan | sim/quan | Dev Lát 3 & 4 | quan |
| osgi23 (QA) | osgi23-qa | client/ui | QA Lead | ui |

**Vai quy trình:** PO (đầu mối hỏi giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead · Scrum/Release. Do các nhóm khác trong lớp đã đủ chỗ (full), `osgi23` làm solo và kiêm nhiệm các vai trò. Khai báo 4 slots theo quy ước module để vượt qua kiểm tra định dạng của `check_team.py`.

## Thỏa thuận làm việc nhóm (điền trong 15 phút kickoff, ≤ 10 dòng)

- Kênh liên lạc: Tự quản lý trên repo cá nhân và trao đổi với giảng viên qua issue / lab board.
- Khi bất đồng về thiết kế: Đối chiếu trực tiếp với PRD-0 và Test Contract v1.0; nếu mơ hồ thì ghi giả định vào `docs/clarify.md`.
- Khi vướng quá 10 phút: Dừng lại kiểm tra test failure, bám sát từng lát cắt (Slice) độc lập.
- Giờ standup giữa phase: Phút 25 và phút 45 mỗi phase.
- Cách đọc code: Tự review diff chi tiết trước khi commit bằng `git diff`.
- Cách làm việc với Git: Commit rõ ràng theo từng lát; test xanh trước khi push; gắn tag `phase-1` trước 1:00.
