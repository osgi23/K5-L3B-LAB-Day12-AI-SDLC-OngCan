"""Buổi tối — Mở Quán.

Cửa hàng nhìn từ trên xuống: vị trí `[x, z]` (z tăng về bắc).

Quy trình một bước:
1. Đồng hồ: giảm timer ca, timer nấu, timer ăn, timer kiên nhẫn.
   Chỉ tăng ready_ticks cho món đã ready ở đầu bước.
2. Bếp: món nấu xong chuyển ready với ready_ticks = 0, phát dish_ready.
3. Di chuyển & tương tác: tối đa MỘT interact (khoảng cách, bếp trước bàn, id).
   - Bếp idle: nhận đơn reserved cũ nhất, trừ kho, chuyển cooking, phát cook_started.
   - Bếp ready: tay trống lấy món, bếp về idle, phát dish_picked.
   - Bàn: tay có món đúng order_id, khách ăn, chốt boa, phát served.
4. Xử lý khách (theo thứ tự id bàn):
   - Ăn xong: trả tiền, cộng uy tín nếu có boa, phát paid.
   - Hết kiên nhẫn: trừ uy tín, phát customer_left, nhả giữ chỗ / hủy món ở bếp/tay.
   - Hết ca: khách ăn trả tiền (closing), khách chờ rời (closing), dọn xong phát quan_end.
5. Khách mới theo lịch (first_customer_tick, customer_interval_s):
   - Bàn trống id nhỏ nhất, chọn đều trong các món đủ nguyên liệu khả dụng; thiếu món phát no_dish.
"""

import math

from ..ids import id_key, sort_by_id
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, day_plan=None,
                 initial_money=0, initial_earned=0, initial_reputation=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        self.day_plan = day_plan
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.phase_tick = 0
        if initial_reputation is not None:
            self.reputation = float(initial_reputation)
        else:
            self.reputation = float(scenario.get("reputation", t["reputation_initial"]))
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            order_id=s.get("order_id"), base_price=s.get("base_price"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.random_customers = scenario.get("random_customers", True)

        self.customers = []
        for c in scenario.get("customers", []):
            cust = dict(c)
            cust.setdefault("state", "waiting")
            cust.setdefault("order_tick", 0)
            cust.setdefault("patience_ticks_left", int(round(t["patience_s"] * 60)))
            cust.setdefault("eat_ticks_left", int(round(t["eat_s"] * 60)))
            cust.setdefault("order_status", "reserved")
            dish_id = cust.get("dish_id")
            if "reserved" not in cust:
                if cust.get("order_status") == "reserved" and dish_id in self.menu:
                    cust["reserved"] = dict(self.menu[dish_id]["recipe"])
                else:
                    cust["reserved"] = {}
            if "base_price" not in cust and dish_id in self.menu:
                cust["base_price"] = self.menu[dish_id]["price"]
            cust.setdefault("tip", 0)
            self.customers.append(cust)
            ids.reserve(cust["id"])

        for s in self.stoves:
            ids.reserve(s["id"])
        for tb in self.tables:
            ids.reserve(tb["id"])

        self.money = initial_money
        self.earned = initial_earned
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # 1. Tăng đồng hồ, giảm timer ca, nấu, ăn và kiên nhẫn.
        # Chỉ tăng ready_ticks cho món đã ready ở đầu bước.
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] -= 1

        for c in self.customers:
            if c["state"] == "eating":
                c["eat_ticks_left"] -= 1
            elif c["state"] == "waiting":
                c["patience_ticks_left"] -= 1

        # 2. Xét bếp theo id. Món nấu xong chuyển ready với ready_ticks = 0.
        for s in sort_by_id(self.stoves):
            if s["state"] == "cooking" and s["cook_ticks_left"] <= 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                events.append(("dish_ready", {
                    "stove_id": s["id"],
                    "order_id": s["order_id"],
                    "dish_id": s["dish"]
                }))

        # 3. Di chuyển rồi xét tối đa một interact
        self._move(inp)

        if inp.pressed("interact"):
            irad = self.t["interact_radius"]
            candidates = []
            for s in self.stoves:
                d = math.dist(self.pos, s["pos"])
                if d <= irad:
                    candidates.append((d, 0, s["id"], "stove", s))
            for tb in self.tables:
                d = math.dist(self.pos, tb["pos"])
                if d <= irad:
                    candidates.append((d, 1, tb["id"], "table", tb))

            if candidates:
                candidates.sort(key=lambda item: (item[0], item[1], id_key(item[2])))
                _, _, _, kind, target = candidates[0]

                if kind == "stove":
                    s = target
                    if s["state"] == "idle":
                        # Bếp idle: lấy đơn reserved cũ nhất theo order_tick rồi id bàn
                        reserved_custs = [c for c in self.customers if c.get("order_status") == "reserved"]
                        if reserved_custs:
                            reserved_custs.sort(key=lambda c: (c.get("order_tick", 0), id_key(c["table_id"])))
                            chosen_cust = reserved_custs[0]
                            dish_id = chosen_cust["dish_id"]
                            recipe = self.menu[dish_id]["recipe"]
                            # Tiêu đúng nguyên liệu giữ
                            for item_k, item_qty in recipe.items():
                                self.stock[item_k] = max(0, self.stock.get(item_k, 0) - item_qty)
                            chosen_cust["reserved"] = {}
                            chosen_cust["order_status"] = "assigned"

                            cook_ticks = int(round(self.menu[dish_id]["cook_s"] * TICK))
                            base_price = self.menu[dish_id]["price"]
                            s["state"] = "cooking"
                            s["dish"] = dish_id
                            s["order_id"] = chosen_cust["id"]
                            s["base_price"] = base_price
                            s["cook_ticks_left"] = cook_ticks
                            s["ready_ticks"] = 0

                            items = []
                            for k, count in recipe.items():
                                items.extend([k] * count)
                            items.sort()

                            events.append(("cook_started", {
                                "stove_id": s["id"],
                                "order_id": chosen_cust["id"],
                                "dish_id": dish_id,
                                "items": items,
                                "base_price": base_price
                            }))
                    elif s["state"] == "ready":
                        # Bếp ready giao món cho tay trống và về idle
                        if self.hand is None:
                            self.hand = {
                                "order_id": s["order_id"],
                                "dish_id": s["dish"],
                                "base_price": s["base_price"]
                            }
                            events.append(("dish_picked", {
                                "stove_id": s["id"],
                                "order_id": s["order_id"],
                                "dish_id": s["dish"]
                            }))
                            s["state"] = "idle"
                            s["dish"] = None
                            s["order_id"] = None
                            s["base_price"] = None
                            s["cook_ticks_left"] = 0
                            s["ready_ticks"] = 0

                elif kind == "table":
                    tb = target
                    cust = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
                    if cust is not None and self.hand is not None:
                        if self.hand.get("order_id") == cust["id"]:
                            # Bàn nhận đúng order_id thì khách ăn với timer đầy.
                            patience_max = int(round(self.t["patience_s"] * TICK))
                            ratio = cust["patience_ticks_left"] / patience_max
                            base_price = self.hand["base_price"]
                            if ratio >= self.t["tip_min_patience_ratio"]:
                                tip = math.floor(base_price * self.t["tip_rate"])
                            else:
                                tip = 0

                            events.append(("served", {
                                "order_id": cust["id"],
                                "table_id": tb["id"],
                                "dish_id": cust["dish_id"],
                                "patience_ticks_left": cust["patience_ticks_left"],
                                "base_price": base_price,
                                "tip": tip
                            }))

                            cust["state"] = "eating"
                            cust["order_status"] = "served"
                            cust["base_price"] = base_price
                            cust["tip"] = tip
                            cust["eat_ticks_left"] = int(round(self.t["eat_s"] * TICK))
                            self.hand = None

        # 4. Theo id bàn, khách ăn xong trả tiền rồi rời bàn ngay...
        tables_sorted = sort_by_id(self.tables)
        customers_to_remove = []

        for tb in tables_sorted:
            cust = next((c for c in self.customers if c["table_id"] == tb["id"]), None)
            if cust is None:
                continue

            if self.time_left_ticks > 0:
                # Nếu ca còn giờ:
                if cust["state"] == "eating" and cust["eat_ticks_left"] <= 0:
                    amount = cust["base_price"] + cust["tip"]
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    if cust["tip"] > 0:
                        self.reputation = min(float(self.t["reputation_max"]), self.reputation + float(self.t["tip_reputation"]))
                    events.append(("paid", {
                        "order_id": cust["id"],
                        "table_id": cust["table_id"],
                        "base_price": cust["base_price"],
                        "tip": cust["tip"],
                        "amount": amount,
                        "reason": "finished_eating"
                    }))
                    customers_to_remove.append(cust)
                elif cust["state"] == "waiting" and cust["patience_ticks_left"] <= 0:
                    self.reputation = max(float(self.t["reputation_min"]), self.reputation + float(self.t["left_reputation_delta"]))
                    events.append(("customer_left", {
                        "order_id": cust["id"],
                        "table_id": cust["table_id"],
                        "reason": "patience",
                        "reputation": self.reputation
                    }))
                    cust["reserved"] = {}
                    # Bỏ món của đơn đang nấu, ready hoặc trên tay
                    if self.hand and self.hand.get("order_id") == cust["id"]:
                        self.hand = None
                    for s in self.stoves:
                        if s.get("order_id") == cust["id"]:
                            s["state"] = "idle"
                            s["dish"] = None
                            s["order_id"] = None
                            s["base_price"] = None
                            s["cook_ticks_left"] = 0
                            s["ready_ticks"] = 0
                    customers_to_remove.append(cust)

            else:
                # Khi hết ca: khách ăn trả ngay, khách chờ rời với closing và không trừ uy tín
                if cust["state"] == "eating":
                    amount = cust["base_price"] + cust["tip"]
                    self.money += amount
                    self.earned += amount
                    self.shift_earned += amount
                    if cust["tip"] > 0:
                        self.reputation = min(float(self.t["reputation_max"]), self.reputation + float(self.t["tip_reputation"]))
                    events.append(("paid", {
                        "order_id": cust["id"],
                        "table_id": cust["table_id"],
                        "base_price": cust["base_price"],
                        "tip": cust["tip"],
                        "amount": amount,
                        "reason": "closing"
                    }))
                elif cust["state"] == "waiting":
                    events.append(("customer_left", {
                        "order_id": cust["id"],
                        "table_id": cust["table_id"],
                        "reason": "closing",
                        "reputation": self.reputation
                    }))
                customers_to_remove.append(cust)

        for c in customers_to_remove:
            if c in self.customers:
                self.customers.remove(c)

        # Nếu hết ca: dọn xong phát quan_end
        if self.time_left_ticks <= 0:
            self.customers.clear()
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation
            }))
            return events

        # 5. Nếu còn giờ, xét lượt khách theo first_customer_tick, rồi mỗi customer_interval_s × 60 tick.
        first_tick = self.t["first_customer_tick"]
        cust_interval = int(round(self.t["customer_interval_s"] * TICK))
        is_customer_tick = (self.phase_tick == first_tick) or (
            self.phase_tick > first_tick and (self.phase_tick - first_tick) % cust_interval == 0
        )

        if is_customer_tick and self.random_customers:
            occupied_tables = {c["table_id"] for c in self.customers}
            empty_tables = [tb for tb in sort_by_id(self.tables) if tb["id"] not in occupied_tables]
            if empty_tables:
                chosen_table = empty_tables[0]
                # Tồn nguyên liệu khả dụng = tồn vật lý trừ phần giữ
                avail_stock = dict(self.stock)
                for c in self.customers:
                    for k, count in c.get("reserved", {}).items():
                        avail_stock[k] = avail_stock.get(k, 0) - count

                # Trong day, lọc menu theo id món trong kế hoạch trước khi lọc nguyên liệu khả dụng.
                allowed_dishes = sorted(self.day_plan["dishes"].keys()) if self.day_plan and "dishes" in self.day_plan else sorted(self.menu.keys())
                fulfillable = []
                for dish_id in allowed_dishes:
                    if dish_id in self.menu:
                        recipe = self.menu[dish_id]["recipe"]
                        if all(avail_stock.get(k, 0) >= count for k, count in recipe.items()):
                            fulfillable.append(dish_id)

                if not fulfillable:
                    events.append(("no_dish", {}))
                else:
                    chosen_dish = self.rng.get("customer_dish").choice(fulfillable)
                    cid = self.ids.new("C")
                    patience_ticks = int(round(self.t["patience_s"] * TICK))
                    eat_ticks = int(round(self.t["eat_s"] * TICK))
                    price = self.menu[chosen_dish]["price"]
                    recipe = dict(self.menu[chosen_dish]["recipe"])
                    cust = {
                        "id": cid,
                        "table_id": chosen_table["id"],
                        "dish_id": chosen_dish,
                        "order_tick": self.phase_tick,
                        "state": "waiting",
                        "patience_ticks_left": patience_ticks,
                        "eat_ticks_left": eat_ticks,
                        "order_status": "reserved",
                        "reserved": recipe,
                        "base_price": price,
                        "tip": 0
                    }
                    self.customers.append(cust)
                    events.append(("customer_arrived", {
                        "order_id": cid,
                        "table_id": chosen_table["id"],
                        "dish_id": chosen_dish
                    }))

        return events

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
