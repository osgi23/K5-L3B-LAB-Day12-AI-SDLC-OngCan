"""Buổi sáng — Lặn & Hái (`gather`, v1.1).

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
Vùng nước x ∈ [0, 100], d ∈ [0, 30]. Nông d < 10, giữa 10 ≤ d < 20, sâu d ≥ 20.
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

    def __init__(self, tuning, scenario, streams, ids, day=1, upgrades=None,
                 initial_money=0, initial_earned=0, initial_reputation=None):
        t = tuning["gather"]
        self.t = t
        self.rng = streams
        self.ids = ids
        self.day = day
        self.upgrades = upgrades or {}
        self.initial_money = initial_money
        self.initial_earned = initial_earned
        self.initial_reputation = initial_reputation

        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))

        # Nâng cấp oxy & máu
        oxy_s = t["oxygen_max_s"]
        if self.upgrades.get("oxygen") == 1:
            oxy_s = 45
        elif self.upgrades.get("oxygen") == 2:
            oxy_s = 60
        self.oxygen_max = int(round(oxy_s * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)

        hp_max = t["hp_max"]
        if self.upgrades.get("hp") == 1:
            hp_max = 4
        elif self.upgrades.get("hp") == 2:
            hp_max = 5
        self.hp_max = hp_max
        self.hp = p.get("hp", self.hp_max)

        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        self.attack_cd_ticks = p.get("attack_cd_ticks", 0)
        self.hold = list(scenario.get("hold", []))
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = 0

        # Nút hái
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]

        # Đàn cá
        self.fish = []
        if "fish" in scenario:
            for f in scenario["fish"]:
                self.fish.append({
                    "id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                    "heading_deg": float(f.get("heading_deg", 0.0)),
                    "age_ticks": int(f.get("age_ticks", 0))
                })
        elif scenario.get("random_fish", True):
            # Khởi tạo 8 đàn cá ở 8 điểm khác nhau
            self.fish = self._init_random_fish(t)

        # Quái vật (Cá Sấu Năm Chèo)
        self.monsters = []
        if "monsters" in scenario:
            for m in scenario["monsters"]:
                self.monsters.append({
                    "id": m["id"],
                    "kind": m.get("kind", "ca_sau"),
                    "pos": [float(c) for c in m["pos"]],
                    "waypoints": [[float(c) for c in wp] for wp in m.get("waypoints", [[m["pos"][0], m["pos"][1]], [m["pos"][0] + 4, m["pos"][1]]])],
                    "target_idx": m.get("target_idx", 1),
                    "state": m.get("state", "patrol"),
                    "state_ticks_left": m.get("state_ticks_left", 0),
                    "recoil_dir": list(m["recoil_dir"]) if m.get("recoil_dir") else None
                })
        else:
            # Lấy quái vật từ tuning theo Ngày
            m_config = t.get("monsters", {})
            for sp in m_config.get("spawns", []):
                if sp.get("from_day", 1) <= self.day:
                    self.monsters.append({
                        "id": sp["id"],
                        "kind": sp.get("kind", "ca_sau"),
                        "pos": [float(c) for c in sp["pos"]],
                        "waypoints": [[float(c) for c in wp] for wp in sp["waypoints"]],
                        "target_idx": 1,
                        "state": "patrol",
                        "state_ticks_left": 0,
                        "recoil_dir": None
                    })

        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])

        self.money = self.initial_money
        self.earned = self.initial_earned
        if self.initial_reputation is not None:
            self.reputation = float(self.initial_reputation)
        else:
            self.reputation = float(tuning["quan"]["reputation_initial"])
        self.done = False
        self.reason = None

    def _init_random_fish(self, t):
        fish_list = []
        # 36 cặp loài - vị trí
        candidates = []
        spawn_x = t.get("fish_spawn_x", [15, 30, 45, 60, 75, 90])
        spawn_d = t.get("fish_spawn_depths", {"ca_linh": [5, 10], "ca_loc": [10, 16], "ca_keo": [24, 27]})
        for k, depths in spawn_d.items():
            for x in spawn_x:
                for d in depths:
                    candidates.append((k, [float(x), float(d)]))

        rng = self.rng.get("fish_spawn")
        rng.shuffle(candidates)

        # Chọn 8 điểm có tọa độ khác nhau
        seen_pos = set()
        for k, pos in candidates:
            pos_key = (pos[0], pos[1])
            if pos_key not in seen_pos:
                seen_pos.add(pos_key)
                fid = self.ids.new("F")
                heading = rng.uniform(0, 360)
                fish_list.append({
                    "id": fid, "kind": k, "pos": list(pos),
                    "heading_deg": heading, "age_ticks": 0
                })
                if len(fish_list) >= t.get("fish_initial", 8):
                    break
        return fish_list

    def inventory_items(self) -> dict:
        return hold_to_items(self.hold)

    def snapshot(self) -> dict:
        return {
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.hp_max, "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": self.hold, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
                     for f in sort_by_id(self.fish)],
            "monsters": [{"id": m["id"], "pos": m["pos"], "kind": m["kind"], "state": m["state"]}
                         for m in sort_by_id(self.monsters)]
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        self.attack_cd_ticks = max(0, self.attack_cd_ticks - 1)

        # 1. Hồi nút cây
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))

        # 2. Bơi người chơi + dive/surface
        was_surface = self._at_surface()
        self._move(inp)
        now_surface = self._at_surface()

        if was_surface and not now_surface:
            events.append(("dive", {"pos": list(self.pos)}))
        elif not was_surface and now_surface:
            events.append(("surface", {"pos": list(self.pos)}))

        # 3. Oxy & ngạt
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

        # 4. Cập nhật Cá Sấu Năm Chèo (di chuyển & va chạm hit)
        hit_occurred = self._update_monsters(events)
        if self.hp <= 0:
            lost = list(reversed(self.hold))
            self.hold.clear()
            events.append(("faint", {"cause": "monster", "lost": lost, "hp": 0}))
            self._finish("fainted", events)
            return events

        # 5. Interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events

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

        # 6. Bắt cá
        if inp.pressed("catch"):
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

        # 7. Hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events

        # 8. Cá bơi & sinh cá theo lịch (chỉ khi còn giờ)
        self._update_fish(events)

        return events

    def _update_monsters(self, events):
        for m in sort_by_id(self.monsters):
            state = m["state"]
            if state == "recoil":
                m["state_ticks_left"] -= 1
                rdir = m.get("recoil_dir", [1.0, 0.0])
                step_dist = 2.0 / 60.0
                m["pos"][0] += rdir[0] * step_dist
                m["pos"][1] += rdir[1] * step_dist
                m["pos"][0] = max(0.0, min(100.0, m["pos"][0]))
                m["pos"][1] = max(10.0, min(30.0, m["pos"][1]))
                if m["state_ticks_left"] <= 0:
                    m["state"] = "patrol"
                    m["recoil_dir"] = None

            elif state in ("patrol", "chase"):
                dist_p = math.dist(m["pos"], self.pos)
                player_in_deep = (self.pos[1] >= 10.0)

                if state == "patrol":
                    if player_in_deep and dist_p <= 10.0:
                        m["state"] = "chase"
                elif state == "chase":
                    if dist_p > 16.0 or not player_in_deep:
                        m["state"] = "patrol"

                if m["state"] == "patrol":
                    target_wp = m["waypoints"][m["target_idx"]]
                    step_dist = 1.0 / 60.0
                    d_wp = math.dist(m["pos"], target_wp)
                    if d_wp <= step_dist:
                        m["pos"] = list(target_wp)
                        m["target_idx"] = 1 - m["target_idx"]
                    else:
                        dx = (target_wp[0] - m["pos"][0]) / d_wp
                        dd = (target_wp[1] - m["pos"][1]) / d_wp
                        m["pos"][0] += dx * step_dist
                        m["pos"][1] += dd * step_dist
                elif m["state"] == "chase":
                    step_dist = 3.0 / 60.0
                    if dist_p > 0:
                        dx = (self.pos[0] - m["pos"][0]) / dist_p
                        dd = (self.pos[1] - m["pos"][1]) / dist_p
                        m["pos"][0] += dx * step_dist
                        m["pos"][1] += dd * step_dist

                m["pos"][0] = max(0.0, min(100.0, m["pos"][0]))
                m["pos"][1] = max(10.0, min(30.0, m["pos"][1]))

        # Va chạm hit sau khi cả hai di chuyển
        if self.pos[1] >= 10.0 and self.invuln_ticks == 0:
            candidates = []
            for m in self.monsters:
                if m["state"] != "recoil":
                    d = math.dist(m["pos"], self.pos)
                    if d <= 1.5:
                        candidates.append((d, m))
            if candidates:
                candidates.sort(key=lambda item: (item[0], id_key(item[1]["id"])))
                hitter = candidates[0][1]

                self.hp -= 1
                lost_count = len(self.hold) // 2
                lost = []
                for _ in range(lost_count):
                    lost.append(self.hold.pop())
                self.invuln_ticks = 90

                events.append(("monster_hit", {
                    "monster_id": hitter["id"],
                    "hp": self.hp,
                    "lost": lost,
                    "pos": list(self.pos)
                }))

                # Con gây hit chuyển sang recoil
                vx = hitter["pos"][0] - self.pos[0]
                vd = hitter["pos"][1] - self.pos[1]
                vlen = math.hypot(vx, vd)
                if vlen == 0:
                    recoil_dir = [1.0, 0.0]
                else:
                    recoil_dir = [vx / vlen, vd / vlen]
                hitter["state"] = "recoil"
                hitter["state_ticks_left"] = 60
                hitter["recoil_dir"] = recoil_dir
                return True
        return False

    def _update_fish(self, events):
        # 1. Cá bơi
        depth_bounds = self.t.get("fish_depths", {
            "ca_linh": [3, 12], "ca_loc": [8, 20], "ca_keo": [22, 28]
        })
        x_min, x_max = self.t.get("fish_x", [4, 96])
        fish_speed = self.t.get("fish_speed", 1.5)
        step_dist = fish_speed / TICK

        for f in self.fish:
            f["age_ticks"] += 1
            if f["age_ticks"] % self.t.get("fish_turn_ticks", 120) == 0:
                f["heading_deg"] = self.rng.get("fish_turn").uniform(0, 360)

            rad = math.radians(f["heading_deg"])
            dx = step_dist * math.cos(rad)
            dd = step_dist * math.sin(rad)
            nx = f["pos"][0] + dx
            nd = f["pos"][1] + dd

            d_min, d_max = depth_bounds.get(f["kind"], [0, 30])
            head = f["heading_deg"]

            # Phản xạ x
            if nx < x_min:
                nx = x_min + (x_min - nx)
                head = (180.0 - head) % 360.0
            elif nx > x_max:
                nx = x_max - (nx - x_max)
                head = (180.0 - head) % 360.0

            # Phản xạ d
            if nd < d_min:
                nd = d_min + (d_min - nd)
                head = (-head) % 360.0
            elif nd > d_max:
                nd = d_max - (nd - d_max)
                head = (-head) % 360.0

            f["pos"][0] = max(float(x_min), min(float(x_max), nx))
            f["pos"][1] = max(float(d_min), min(float(d_max), nd))
            f["heading_deg"] = head

        # 2. Sinh cá theo lịch
        spawn_interval = self.t.get("fish_spawn_ticks", 360)
        fish_max = self.t.get("fish_max", 12)
        if self.phase_tick >= spawn_interval and self.phase_tick % spawn_interval == 0:
            if len(self.fish) < fish_max:
                clearance = self.t.get("fish_spawn_clearance", 1.0)
                spawn_x = self.t.get("fish_spawn_x", [15, 30, 45, 60, 75, 90])
                spawn_d = self.t.get("fish_spawn_depths", {
                    "ca_linh": [5, 10], "ca_loc": [10, 16], "ca_keo": [24, 27]
                })

                valid_by_species = {}
                for sp, depths in spawn_d.items():
                    valid_pts = []
                    for sx in spawn_x:
                        for sd in depths:
                            pt = [float(sx), float(sd)]
                            if all(math.dist(pt, cur_f["pos"]) > clearance for cur_f in self.fish):
                                valid_pts.append(pt)
                    if valid_pts:
                        valid_by_species[sp] = valid_pts

                if valid_by_species:
                    weights = self.t.get("fish_weights", {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3})
                    total_w = sum(weights[sp] for sp in valid_by_species)
                    norm_weights = {sp: weights[sp] / total_w for sp in valid_by_species}

                    rng = self.rng.get("fish_spawn")
                    r = rng.random()
                    cum = 0.0
                    chosen_species = None
                    for sp, w in norm_weights.items():
                        cum += w
                        if r <= cum:
                            chosen_species = sp
                            break
                    if chosen_species is None:
                        chosen_species = list(valid_by_species.keys())[-1]

                    chosen_pos = rng.choice(valid_by_species[chosen_species])
                    heading = rng.uniform(0, 360)
                    new_id = self.ids.new("F")
                    self.fish.append({
                        "id": new_id, "kind": chosen_species, "pos": list(chosen_pos),
                        "heading_deg": heading, "age_ticks": 0
                    })
                    events.append(("fish_spawned", {
                        "id": new_id, "kind": chosen_species, "pos": list(chosen_pos)
                    }))

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
