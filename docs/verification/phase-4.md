# Báo cáo nghiệm thu Phase 4 — Phát hành v1.0.0

**Thời gian nghiệm thu:** 2026-11-21  
**Môi trường:** Python 3.14 (Windows / Linux / macOS)  
**Hợp đồng mục tiêu:** Test Contract v1.3 (`game.contract.json`, `chonoi/__init__.py`)  
**Commit bàn giao:** Khớp với tag `phase-4` và `v1.0.0` trên nhánh `main`.

---

## 1. Ma trận tiêu chí chấp nhận (Acceptance Criteria Matrix)

| Mã AC | Tiêu chí nghiệm thu | Bằng chứng kiểm chứng | Kết quả |
|---|---|---|---|
| **AC-P4-01** | Khai báo `contract_version: "1.3"` và `bench_cmd`, `soak_cmd` ở gốc `game.contract.json`. | [game.contract.json](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/game.contract.json#L2-L8), [test_phase4_rules.py](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/tests/test_phase4_rules.py#L30-L36) | **PASS** |
| **AC-P4-02** | Khai báo extension `leaderboard` trong mảng `extensions` của contract. | [game.contract.json](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/game.contract.json#L9-L11), `test_01_contract_v13_declaration` | **PASS** |
| **AC-P4-03** | Lệnh benchmark chạy với `--seed`, `--duration`, `--out`, đo đạc đúng cảnh sáng lõi với Cá Sấu Năm Chèo và Út Sen đứng yên. | [bench.py](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/chonoi/bench.py), `test_02_benchmark_command_output_structure` | **PASS** |
| **AC-P4-04** | Benchmark xuất đúng 5 trường JSON: `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`. | [bench.json](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-4/bench.json), `test_02_benchmark_command_output_structure` | **PASS** |
| **AC-P4-05** | Hiệu năng benchmark đạt chuẩn: `avg_fps >= 60`, `p1_low_fps >= 30`, `load_ms <= 10000`. | Kết quả đo thực tế: `avg_fps: 69`, `p1_low_fps: 63`, `load_ms: 1` | **PASS** |
| **AC-P4-06** | Lệnh soak chạy 10 ngày trong một tiến trình headless với `--seed`, `--days`, `--out`. | [soak.py](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/chonoi/soak.py), `test_03_soak_headless_multi_day_loop` | **PASS** |
| **AC-P4-07** | Kế hoạch ngày D1-D5 lặp ở Ngày 6-10 trong DaySim. | [day.py](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/chonoi/sim/day.py#L48-L50), `test_03_soak_headless_multi_day_loop` | **PASS** |
| **AC-P4-08** | Soak xuất đúng cấu trúc: `days`, `days_completed`, `crashes`, `results`, `duration_s`. Đạt `days_completed = days` và `crashes = 0`. | [soak.json](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-4/soak.json): 10 ngày hoàn tất, 0 crash, thời gian 1.2s | **PASS** |
| **AC-P4-09** | Cảnh báo thủy quái gần / rượt đuổi hiển thị rõ ràng bằng chữ và biểu tượng. | [index.html](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/chonoi/web/index.html#L210-L225) (`⚠️ CẢNH BÁO: THỦY QUÁI GẦN! CÁ SẤU ĐANG RƯỢT!`) | **PASS** |
| **AC-P4-10** | Cảnh báo oxy nguy cấp (< 5s dưới nước) hiển thị nhấp nháy chữ + icon. | [index.html](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/chonoi/web/index.html#L227-L238) (`💨 OXY SẮP HẾT: NGOI LÊN GẤP!`) | **PASS** |
| **AC-P4-11** | Cảnh báo khách chờ sắp giận (kiên nhẫn <= 25%) hiển thị trong Quán. | [index.html](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/chonoi/web/index.html#L295-L306) (`😡 CẢNH BÁO: KHÁCH BÀN ... SẮP HẾT KIÊN NHẪN!`) | **PASS** |
| **AC-P4-12** | Chế độ tương phản cao (High Contrast Mode) bật tắt bằng phím `C` và nút trên màn hình, cả 3 cảnh báo hoạt động rõ nét. | [index.html](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/chonoi/web/index.html#L63-L80) | **PASS** |
| **AC-P4-13** | Phụ đề SFX hiển thị mô tả âm thanh hành động theo thời gian thực ở đáy màn hình. | [index.html](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/chonoi/web/index.html#L110-L125) (`drawSfxSubtitle`) | **PASS** |
| **AC-P4-14** | Bảng xếp hạng cục bộ lưu bền vững top 10, sắp xếp điểm giảm dần ổn định, cặp cờ hợp lệ, xuất qua `--export-leaderboard`. | [leaderboard.py](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/chonoi/leaderboard.py), `test_04_leaderboard_cli_pair_and_mode_validation`, `test_05_leaderboard_storage_sorting_and_export` | **PASS** |
| **AC-P4-15** | Toàn bộ các bài test hồi quy từ Phase 1 đến Phase 3 và Phase 4 đều đạt (60/60 tests OK). | [test.log](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-4/test.log) (Ran 60 tests in 9.455s - OK) | **PASS** |

---

## 2. Bằng chứng kiểm thử đính kèm
- File kết quả đo benchmark: [bench.json](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-4/bench.json)
- File kết quả kiểm thử độ bền soak 10 ngày: [soak.json](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-4/soak.json)
- Nhật ký toàn bộ 60 bài kiểm thử: [test.log](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/proof/phase-4/test.log)
- File hướng dẫn phát hành: [release-v1.0.0.md](file:///d:/VIN/K5-L3B-LAB-Day12-AI-SDLC-OngCan/docs/release-v1.0.0.md)
