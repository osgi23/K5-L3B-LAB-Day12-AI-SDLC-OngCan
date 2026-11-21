"""File kho v1.2 (Contract G): {"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}.

Đọc: từ chối file kho đếm loại cũ, sai schema, kind lạ, id trùng, fresh ngoài [0, 100] (BadInput -> mã 2).
Ghi: qua file tạm cùng thư mục rồi thay thế nguyên tử, xuất theo thứ tự id, byte-ổn-định.
"""

import json
import math
import os
import tempfile

from .errors import BadInput
from .ids import id_key

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_P2 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")
KINDS = KINDS_P2


def validate_items(items, kinds=KINDS) -> list:
    if isinstance(items, dict):
        raise BadInput("kho v1.2 phải là mảng cá thể ({'items': [...]}), không dùng kho đếm loại")
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể")

    out = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            raise BadInput("mỗi cá thể trong items phải là object")
        if set(item.keys()) != {"id", "kind", "fresh"}:
            raise BadInput(f"cá thể phải có đúng các khóa id, kind, fresh: {list(item.keys())}")

        iid = item.get("id")
        if not isinstance(iid, str) or not iid:
            raise BadInput("id cá thể phải là chuỗi khác rỗng")
        if iid in seen:
            raise BadInput(f"id cá thể bị trùng: {iid}")
        seen.add(iid)

        kind = item.get("kind")
        if kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind}")

        fresh = item.get("fresh")
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float)):
            raise BadInput(f"độ tươi phải là số: {fresh!r}")
        if math.isnan(fresh) or math.isinf(fresh) or not (0.0 <= fresh <= 100.0):
            raise BadInput(f"độ tươi phải hữu hạn trong [0, 100]: {fresh}")

        out.append({
            "id": iid,
            "kind": kind,
            "fresh": float(fresh) if isinstance(fresh, (int, float)) else fresh
        })
    return out


def read_inventory(path: str, kinds=KINDS) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    return validate_items(data["items"], kinds)


def hold_to_items(hold: list) -> list:
    """Mảng cá thể trong khoang -> mảng cá thể xuất kho, sắp theo id_key."""
    sorted_items = sorted(hold, key=lambda it: id_key(it["id"]))
    return [{
        "id": it["id"],
        "kind": it["kind"],
        "fresh": round(it["fresh"], 3) if isinstance(it["fresh"], float) else it["fresh"]
    } for it in sorted_items]


def write_inventory(path: str, items: list):
    sorted_items = sorted(items, key=lambda it: id_key(it["id"]))
    clean_items = [{
        "id": it["id"],
        "kind": it["kind"],
        "fresh": round(it["fresh"], 3) if isinstance(it["fresh"], float) else it["fresh"]
    } for it in sorted_items]

    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": clean_items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
