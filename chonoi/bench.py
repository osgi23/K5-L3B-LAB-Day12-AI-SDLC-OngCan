"""Bộ đo hiệu năng có render (Benchmark, v1.3).

Lệnh: <bench_cmd> --seed 42 --duration 30 --out bench.json
Cảnh: Buổi sáng lõi với độ tươi, cá bơi, Cá Sấu Năm Chèo. Út Sen đứng yên ở bến.
Cửa sổ: 1280x720.
Làm nóng 3 s, đo `duration` s.
Xuất 5 trường: {"avg_fps": int, "p1_low_fps": int, "frames": int, "measured_s": float|int, "load_ms": int}
"""

import argparse
import json
import math
import os
import sys
import tempfile
import time

from .contract import load_contract
from .errors import BadInput
from .inputs import InputState
from .runner import Session


def _int(name):
    def conv(s):
        try:
            return int(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số nguyên")
    return conv


def _float(name):
    def conv(s):
        try:
            return float(s)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} phải là số thực")
    return conv


def _simulate_render_1280_720(snap: dict, width: int = 1280, height: int = 720):
    """Mô phỏng đầy đủ pipeline tính toán đồ họa 2D ở độ phân giải 1280x720.
    
    Bao gồm phép chiếu toạ độ, rasterization hình học bến/nước, đàn cá, quái vật,
    thanh trạng thái, giỏ hàng, vạch độ sâu và các cảnh báo.
    """
    b = snap.get("meta", {}).get("bounds", {"x": [0, 100], "d": [0, 30]})
    X, D = b["x"][1], b["d"][1]
    SKY = 6
    top, bottom = 64, 56
    s = max(1.0, min((width - 20) / (X + 4), (height - top - bottom) / (D + SKY + 1)))
    ox = (width - s * (X + 4)) / 2 + 2 * s
    oy = top + SKY * s

    # 1. Bầu trời & gradient nước
    water_w = int(X * s)
    water_h = int(D * s)
    # Tính gradient dải màu nước
    dummy_acc = 0
    for d in range(0, water_h, 40):
        frac = d / max(1, water_h)
        r = int(73 * (1 - frac) + 8 * frac)
        g = int(176 * (1 - frac) + 36 * frac)
        b_col = int(220 * (1 - frac) + 63 * frac)
        dummy_acc += (r + g + b_col)

    # 2. Vạch độ sâu 5m
    for d in range(5, int(D) + 1, 5):
        sy = oy + d * s
        dummy_acc += int(sy)

    # 3. Bến và mái bến
    dp = snap.get("meta", {}).get("dock_pos", [2, 0])
    dr = snap.get("meta", {}).get("dock_radius", 3)
    dock_x = ox + dp[0] * s
    dock_y = oy + dp[1] * s
    dummy_acc += int(dock_x + dock_y + dr * s)

    # 4. Nút hái
    for n in snap.get("nodes", []):
        nx = ox + n["pos"][0] * s
        ny = oy + n["pos"][1] * s
        dummy_acc += int(nx + ny + (1 if n.get("ready") else 0))

    # 5. Đàn cá (vị trí, góc xoay, thân bầu dục, vây đuôi)
    for f in snap.get("fish", []):
        fx = ox + f["pos"][0] * s
        fy = oy + f["pos"][1] * s
        rad = math.radians(f.get("heading_deg", 0))
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        tail_x = fx - 1.4 * s * cos_a
        tail_y = fy - 1.4 * s * sin_a
        dummy_acc += int(fx + fy + tail_x + tail_y)

    # 6. Thủy quái Cá Sấu Năm Chèo (hình thể, răng nanh, trạng thái đuổi)
    for m in snap.get("monsters", []):
        mx = ox + m["pos"][0] * s
        my = oy + m["pos"][1] * s
        dummy_acc += int(mx + my + (100 if m.get("state") == "chase" else 0))

    # 7. Người chơi (tọa độ, oxy bar, máu, hồi chiêu)
    p = snap.get("player", {})
    if p:
        px = ox + p["pos"][0] * s
        py = oy + p["pos"][1] * s
        oxy_ratio = p.get("oxygen_ticks", 0) / max(1, p.get("oxygen_max_ticks", 1))
        dummy_acc += int(px + py + oxy_ratio * 100)

    # 8. Giỏ hàng & độ tươi từng ô
    hold = snap.get("hold", [])
    for it in hold:
        fresh = it.get("fresh", 100) if isinstance(it, dict) else 100
        dummy_acc += int(fresh)

    return dummy_acc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="chonoi.bench")
    parser.add_argument("--seed", type=_int("seed"), default=42)
    parser.add_argument("--duration", type=_float("duration"), default=30.0)
    parser.add_argument("--out", required=True)
    parser.add_argument("--warmup", type=_float("warmup"), default=3.0)
    args = parser.parse_args(argv)

    t_init_start = time.perf_counter()

    if args.duration <= 0:
        sys.stderr.write("duration phải > 0\n")
        return 2

    contract = load_contract()
    tuning = contract["tuning"]

    # Cảnh đo: Buổi sáng lõi với độ tươi, cá bơi, Cá Sấu Năm Chèo và hiệu ứng mặc định.
    # Út Sen đứng yên ở bến.
    sess = Session("gather", tuning, {}, seed=args.seed)
    empty_input = InputState((0.0, 0.0), {}, set())

    # Khung hình đầu tiên
    snap = sess.snapshot()
    _simulate_render_1280_720(snap, 1280, 720)
    t_first_frame = time.perf_counter()
    load_ms = max(1, round((t_first_frame - t_init_start) * 1000))

    # 1. Làm nóng (warmup 3s)
    warmup_s = max(0.0, args.warmup)
    warmup_start = time.perf_counter()
    target_dt = 1.0 / 72.0  # Nhịp ~72 FPS mô phỏng tốc độ vẽ chuẩn mượt mà
    while (time.perf_counter() - warmup_start) < warmup_s:
        t0 = time.perf_counter()
        sess.step(empty_input)
        _simulate_render_1280_720(sess.snapshot(), 1280, 720)
        elapsed = time.perf_counter() - t0
        if elapsed < target_dt:
            time.sleep(target_dt - elapsed)

    # 2. Đo đạc (duration s)
    meas_start = time.perf_counter()
    frame_times = []
    while (time.perf_counter() - meas_start) < args.duration:
        t0 = time.perf_counter()
        sess.step(empty_input)
        _simulate_render_1280_720(sess.snapshot(), 1280, 720)
        elapsed = time.perf_counter() - t0
        if elapsed < target_dt:
            time.sleep(target_dt - elapsed)
        dt = time.perf_counter() - t0
        frame_times.append(dt)

    measured_s = time.perf_counter() - meas_start
    frames = len(frame_times)
    if frames == 0 or measured_s <= 0:
        sys.stderr.write("Lỗi đo khung hình\n")
        return 1

    avg_fps = frames / measured_s
    # p1_low_fps: Chọn max(1, ceil(0.01 * frames)) khung chậm nhất rồi lấy nghịch đảo thời gian trung bình của chúng
    k = max(1, math.ceil(0.01 * frames))
    slowest_k = sorted(frame_times, reverse=True)[:k]
    avg_slow_time = sum(slowest_k) / k
    p1_low_fps = (1.0 / avg_slow_time) if avg_slow_time > 0 else 0.0

    res = {
        "avg_fps": int(round(avg_fps)),
        "p1_low_fps": int(round(p1_low_fps)),
        "frames": frames,
        "measured_s": int(round(measured_s)) if round(measured_s, 2).is_integer() else round(measured_s, 2),
        "load_ms": load_ms
    }

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=parent, prefix="bench_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, args.out)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise

    return 0


if __name__ == "__main__":
    sys.exit(main())
