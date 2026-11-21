"""Buổi sáng — Lặn & Hái (`gather`).

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Quy trình một bước:
1. Đồng hồ & bộ đếm: giảm timer ca, hồi chiêu bắt cá, hồi nút cây (từ 1 về 0 phát node_regrown).
2. Bơi + chặn biên: phát dive / surface khi đổi phía biên mặt nước (d = surface_depth).
3. Tính oxy theo d cuối bước:
   - Mặt nước hồi oxy, reset ngạt.
   - Dưới nước trừ 1 tick; chạm 0 phát oxygen_empty; đếm ngạt đủ choke_interval_ticks thì -1 Máu, phát choke.
   - Hết máu (hp = 0) ngất: bỏ giỏ (LIFO), phát faint, kết thúc với fainted và kho rỗng.
4. Interact: bến trước (docked), rồi hái nút ready gần nhất tại mặt nước (gather / hold_full).
5. Catch: dưới nước và hết hồi, bắt đàn cá gần nhất (fish_caught / hold_full).
6. Hết giờ: kết thúc time.
"""

import math

from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))  # thứ tự nhặt, cuối mảng là mới nhất
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif scenario.get("random_fish", True):
            src_fish = t["fish_initial"]
        else:
            src_fish = []
        # Đàn cá đứng yên ở phase này. Cá bơi / sinh thêm là việc của phase sau.
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0)} for f in src_fish]
        for coll in (self.nodes, self.fish):
            for e in coll:
                ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    # --- giao diện cho runner -------------------------------------------------
    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
                     for f in sort_by_id(self.fish)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))

        # 2. bơi + chặn mép
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()

        # So phân vùng đầu/cuối bước -> dive / surface (data: pos sau di chuyển)
        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and now_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        # Tính oxy theo d CUỐI bước
        if now_surface:
            refill = self.t.get("oxygen_refill_per_tick", 6)
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + refill)
            self.zero_oxy_ticks = 0
        else:
            old_oxy = self.oxygen_ticks
            self.oxygen_ticks = max(0, self.oxygen_ticks - 1)
            if old_oxy > 0 and self.oxygen_ticks == 0:
                events.append(("oxygen_empty", {"oxygen_ticks": 0}))

            if self.oxygen_ticks == 0:
                self.zero_oxy_ticks += 1
                choke_interval = self.t.get("choke_interval_ticks", 60)
                if self.zero_oxy_ticks >= choke_interval:
                    self.zero_oxy_ticks = 0
                    self.hp -= 1
                    events.append(("choke", {"hp": self.hp}))
                    if self.hp <= 0:
                        lost = list(reversed(self.hold))
                        self.hold.clear()
                        events.append(("faint", {"cause": "choke", "lost": lost, "hp": 0}))
                        self._finish("fainted", events)
                        return events

        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events

            # Ngoài bến: chỉ hái khi ở mặt nước
            if self._at_surface():
                irad = self.t["interact_radius"]
                ready_nodes = [n for n in self.nodes if n["regrow_ticks"] == 0]
                candidates = []
                for n in ready_nodes:
                    d = math.dist(self.pos, n["pos"])
                    if d <= irad:
                        candidates.append((d, n))
                if candidates:
                    candidates.sort(key=lambda item: (item[0], id_key(item[1]["id"])))
                    chosen_node = candidates[0][1]
                    nyield = self.t.get("node_yield", 1)
                    cap = self.t["hold_capacity"]
                    free = cap - len(self.hold)
                    if free < nyield:
                        events.append(("hold_full", {
                            "action": "gather",
                            "node_id": chosen_node["id"],
                            "required": nyield,
                            "free": free
                        }))
                    else:
                        for _ in range(nyield):
                            self.hold.append(chosen_node["kind"])
                        chosen_node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {
                            "node_id": chosen_node["id"],
                            "kind": chosen_node["kind"],
                            "amount": nyield
                        }))

        # 4. bắt cá
        if inp.pressed("catch"):
            # chỉ khi catch_cd_ticks == 0 và dưới nước:
            if self.catch_cd_ticks == 0 and not self._at_surface():
                crad = self.t["catch_radius"]
                candidates = []
                for f in self.fish:
                    d = math.dist(self.pos, f["pos"])
                    if d <= crad:
                        candidates.append((d, f))
                if candidates:
                    candidates.sort(key=lambda item: (item[0], id_key(item[1]["id"])))
                    chosen_fish = candidates[0][1]
                    fyield = self.t["fish_yield"][chosen_fish["kind"]]
                    cap = self.t["hold_capacity"]
                    free = cap - len(self.hold)
                    if free < fyield:
                        events.append(("hold_full", {
                            "action": "catch",
                            "fish_id": chosen_fish["id"],
                            "required": fyield,
                            "free": free
                        }))
                    else:
                        for _ in range(fyield):
                            self.hold.append(chosen_fish["kind"])
                        self.fish.remove(chosen_fish)
                        events.append(("fish_caught", {
                            "fish_id": chosen_fish["id"],
                            "kind": chosen_fish["kind"],
                            "yield": fyield
                        }))
                        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))

        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
        return events

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        events.append(("gather_end", {"reason": reason, "inventory": {"items": self.inventory_items()}}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
