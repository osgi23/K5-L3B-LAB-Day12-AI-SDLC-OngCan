"""Bảng xếp hạng cục bộ (Leaderboard, v1.3).

Lưu bền vững top 10 cục bộ. Chỉ ghi một mục cho mỗi lượt chuẩn đủ 5 Ngày.
Sắp điểm giảm dần, hòa thì mục ghi trước đứng trước (stable sort).
Mỗi mục: {"name": str, "score": int, "days_completed": int, "seed": int}
"""

import json
import os
import tempfile
from .errors import BadInput


def load_leaderboard(store_path: str) -> dict:
    if not store_path or not os.path.exists(store_path):
        return {"entries": []}
    try:
        with open(store_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict) or "entries" not in data or not isinstance(data["entries"], list):
                return {"entries": []}
            return data
    except (OSError, ValueError):
        return {"entries": []}


def save_leaderboard(store_path: str, data: dict):
    parent = os.path.dirname(os.path.abspath(store_path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=parent, prefix="lb_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, store_path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def record_entry(store_path: str, name: str, score: int, days_completed: int, seed: int):
    if not isinstance(name, str) or not name.strip():
        raise BadInput("Tên người chơi phải là chuỗi Unicode khác rỗng")
    
    data = load_leaderboard(store_path)
    entries = list(data.get("entries", []))

    new_entry = {
        "name": name.strip(),
        "score": int(score),
        "days_completed": int(days_completed),
        "seed": int(seed)
    }
    entries.append(new_entry)
    # Sắp xếp điểm giảm dần; python sort là stable nên mục ghi trước giữ nguyên thứ tự khi bằng điểm
    entries.sort(key=lambda it: it["score"], reverse=True)
    # Chỉ giữ top 10
    data["entries"] = entries[:10]
    save_leaderboard(store_path, data)
    return data


def export_leaderboard(store_path: str, out_path: str):
    data = load_leaderboard(store_path)
    entries = list(data.get("entries", []))
    entries.sort(key=lambda it: it["score"], reverse=True)
    out_data = {"entries": entries[:10]}
    parent = os.path.dirname(os.path.abspath(out_path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=parent, prefix="exp_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(out_data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, out_path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
