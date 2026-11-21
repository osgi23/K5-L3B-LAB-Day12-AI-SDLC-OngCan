"""Nạp và kiểm scenario (Contract D, v1.1).

Kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
Hỗ trợ cả ba mode: gather, quan, day.
"""

import json

from .errors import BadInput
from .inventory import KINDS, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks", "monsters"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks", "attack_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish", "monsters"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(k not in KINDS for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp", "attack_cd_ticks"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])

    for m in b.get("monsters", []):
        if "pos" in m:
            _pos(f"monsters.{m['id']}.pos", m["pos"], bounds)
        if "waypoints" in m:
            if not isinstance(m["waypoints"], list) or len(m["waypoints"]) != 2:
                raise BadInput(f"monsters.{m['id']}.waypoints phải là mảng 2 waypoint")
            for wp in m["waypoints"]:
                _pos(f"monsters.{m['id']}.wp", wp, bounds)
        if "target_idx" in m and m["target_idx"] not in (0, 1):
            raise BadInput(f"monsters.{m['id']}.target_idx phải là 0 hoặc 1")
        if "state" in m and m["state"] not in ("patrol", "chase", "recoil", "stunned"):
            raise BadInput(f"monsters.{m['id']}.state không hợp lệ")
        if "state_ticks_left" in m:
            _nonneg_int(f"monsters.{m['id']}.state_ticks_left", m["state_ticks_left"])


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"], kinds=KINDS)
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    for c in b.get("customers", []):
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if not isinstance(data, dict):
        raise BadInput("scenario phải là object")

    valid_modes = {"gather", "quan", "day"}
    if mode not in valid_modes:
        raise BadInput(f"mode không hợp lệ: {mode}")

    allowed_blocks = {"gather", "quan", "day"}
    if set(data) - allowed_blocks:
        raise BadInput(f"khối lạ trong scenario: {sorted(set(data) - allowed_blocks)}")

    if mode in ("gather", "quan"):
        if set(data) - {mode}:
            raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
        block = data.get(mode, {})
        if not isinstance(block, dict):
            raise BadInput(f"khối {mode} phải là object")
        allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
        extra = set(block) - allowed
        if extra:
            raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
        dur = int(round(tuning[mode]["duration_s"] * 60))
        if "time_left_ticks" in block:
            t = block["time_left_ticks"]
            if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
                raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
        if mode == "gather":
            _validate_gather(block, tuning)
        else:
            _validate_quan(block, tuning)
        return block

    # mode == "day"
    if "quan" in data:
        if "stock" in data["quan"] or "reputation" in data["quan"]:
            raise BadInput("cấm quan.stock và quan.reputation khi chạy day")
        _validate_quan(data["quan"], tuning)
    if "gather" in data:
        _validate_gather(data["gather"], tuning)
    if "day" in data:
        day_block = data["day"]
        if not isinstance(day_block, dict):
            raise BadInput("khối day phải là object")
        extra = set(day_block) - DAY_KEYS
        if extra:
            raise BadInput(f"trường lạ trong khối day: {sorted(extra)}")
        money = day_block.get("money", 0)
        earned = day_block.get("earned", 0)
        _nonneg_int("day.money", money)
        _nonneg_int("day.earned", earned)
        if money > earned:
            raise BadInput("day.money không được lớn hơn day.earned")
    return data
