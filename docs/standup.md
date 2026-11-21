# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| Phase 1 | Nguyễn Mạnh Quân (osgi23) | Kickoff, phân vai solo, hoàn thiện sim/gather.py và sim/quan.py | Viết test kiểm chứng AC và chạy smoke hai tiến trình | Môi trường Windows cần alias python3; đã xử lý |
| Phase 1 | Nguyễn Mạnh Quân (osgi23) | Đạt 40/40 tests, lưu bằng chứng proof/phase-1/test.log | Hoàn thiện tài liệu nghiệm thu, commit và gắn tag phase-1 | Không vướng gì |
| Phase 2 (phút 20) | Nguyễn Mạnh Quân (osgi23) | Cập nhật v1.1, số chuẩn, cá bơi/sinh, Cá Sấu Năm Chèo, 2 bếp/4 bàn, 6 món | Làm tiếp Shop, DaySim và cơ chế Pause | Cần lưu ý thứ tự xử lý cạnh pause trước khi bước tick |
| Phase 2 (phút 45) | Nguyễn Mạnh Quân (osgi23) | Hoàn thiện DaySim, ShopSim, Pause/Resume, đạt 45/45 tests | Chạy smoke test vòng ngày, lưu proof, tài liệu nghiệm thu và tag phase-2 | Không vướng gì |
| Phase 3 (phút 15) | Nguyễn Mạnh Quân (osgi23) | Soạn ADR-0001, nâng cấp Test Contract v1.2, chuyển đổi kho cá thể và kịch bản | Lập trình logic hao tươi trong gather.py và quan.py | Phải từ chối kho đếm cũ bằng mã 2 |
| Phase 3 (phút 30) | Nguyễn Mạnh Quân (osgi23) | Hoàn thiện hao tươi, spoiled, re-reserve, giá động, HUD, đạt 55/55 tests | Lưu proof nghiệm thu, hoàn thiện tài liệu, commit và gắn tag phase-3 | Không vướng gì |
| Phase 4 (phút 15) | Nguyễn Mạnh Quân (osgi23) | Khai báo Contract v1.3, lập trình `bench.py`, `soak.py`, `leaderboard.py`, cập nhật cảnh báo UI | Chạy benchmark 30s và soak 10 ngày để lấy bằng chứng thực nghiệm | Cần sửa bot soak gọi đúng `sim.pos` thay vì `sim.player["pos"]` |
| Phase 4 (phút 25) | Nguyễn Mạnh Quân (osgi23) | Đạt 60/60 tests xanh, lưu proof bench.json, soak.json, test.log, đóng gói zip | Hoàn thành Release Notes, cập nhật retro, commit, tag phase-4 và v1.0.0 | Không vướng gì, sẵn sàng phát hành |
