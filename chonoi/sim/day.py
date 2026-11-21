"""Vòng ngày hoàn chỉnh (`day`, v1.1).

Quản lý chu kỳ ngày: DayIntro -> gather -> quan -> shop -> Day d+1 (hoặc kết thúc).
Hỗ trợ từ 1 đến 5 ngày.
"""

from ..errors import BadInput
from ..ids import IdAllocator
from ..inventory import hold_to_items
from ..rng import Streams
from .gather import GatherSim
from .quan import QuanSim
from .shop import ShopSim


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.scenario = scenario or {}
        self.streams = streams
        self.ids = ids
        self.days = days
        self.day = 1
        self.days_completed = 0
        self.done = False
        self.reason = None

        day_scen = self.scenario.get("day", {})
        self.money = day_scen.get("money", 0)
        self.earned = day_scen.get("earned", 0)
        self.reputation = float(day_scen.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = dict(day_scen.get("upgrades", {"oxygen": 0, "hp": 0}))
        self.active_upgrades = dict(self.upgrades)

        self.phase = "gather"
        self.stock = {}
        self._init_day(self.day)

    def _get_day_plan(self, d: int) -> dict:
        scen_plans = self.scenario.get("day", {}).get("day_plan", [])
        plan_entry = next((p for p in scen_plans if p.get("day") == d), None)
        if plan_entry is None:
            tuning_plans = self.tuning.get("day_plan", [])
            plan_entry = next((p for p in tuning_plans if p.get("day") == d), None)

        if plan_entry is None:
            return {"dishes": {}, "ingredients": {}}

        dishes = dict(plan_entry["dishes"])
        ingredients = {}
        menu = self.tuning.get("menu", {})
        for dish, qty in dishes.items():
            if dish not in menu:
                raise BadInput(f"món {dish} trong day_plan không có trong menu")
            rec = menu[dish]["recipe"]
            for ing, count in rec.items():
                ingredients[ing] = ingredients.get(ing, 0) + count * qty
        sorted_ing = {k: ingredients[k] for k in sorted(ingredients)}
        if "ingredients" in plan_entry:
            declared_ing = {k: plan_entry["ingredients"][k] for k in sorted(plan_entry["ingredients"])}
            if declared_ing != sorted_ing:
                raise BadInput(f"day_plan.ingredients không khớp công thức dishes ngày {d}")
        return {"dishes": dishes, "ingredients": sorted_ing}

    def _init_day(self, d: int):
        self.current_day_plan = self._get_day_plan(d)
        self.active_upgrades = dict(self.upgrades)
        self.phase = "gather"

        # Khởi tạo gather sim
        g_scen = dict(self.scenario.get("gather", {}))
        if d > 1:
            # Các ngày sau: giỏ làm mới, máu và oxy hồi đầy
            g_scen.pop("hold", None)
            if "player" in g_scen:
                p = dict(g_scen["player"])
                p.pop("hp", None)
                p.pop("oxygen_ticks", None)
                g_scen["player"] = p

        self.sub_sim = GatherSim(
            self.tuning, g_scen, self.streams, self.ids,
            day=d, upgrades=self.active_upgrades,
            initial_money=self.money, initial_earned=self.earned,
            initial_reputation=self.reputation
        )

    def initial_events(self) -> list:
        return [
            ("gather", "day_start", {}, self.day),
            ("gather", "day_plan", dict(self.current_day_plan), self.day),
            ("gather", "phase_start", {}, self.day)
        ]

    @property
    def time_left_ticks(self) -> int:
        return self.sub_sim.time_left_ticks

    @property
    def phase_tick(self) -> int:
        return self.sub_sim.phase_tick

    def snapshot(self) -> dict:
        s = {
            "day": self.day,
            "day_plan": dict(self.current_day_plan),
            "upgrades": dict(self.upgrades),
            "active_upgrades": dict(self.active_upgrades),
        }
        s.update(self.sub_sim.snapshot())
        return s

    def step(self, inp) -> list:
        if self.done:
            return []

        current_day = self.day
        raw_events = self.sub_sim.step(inp)
        out_events = []
        for ev in raw_events:
            if len(ev) == 2:
                out_events.append((self.phase, ev[0], ev[1], current_day))
            elif len(ev) == 3:
                out_events.append((ev[0], ev[1], ev[2], current_day))
            else:
                out_events.append(ev)

        # Xử lý chuyển phase
        if self.phase == "gather" and self.sub_sim.done:
            # Ca lặn kết thúc
            if self.sub_sim.reason == "fainted":
                self.stock = {}
            else:
                self.stock = self.sub_sim.inventory_items()

            self.phase = "quan"
            q_scen = dict(self.scenario.get("quan", {}))
            self.sub_sim = QuanSim(
                self.tuning, q_scen, self.streams, self.ids,
                inventory=self.stock, day_plan=self.current_day_plan,
                initial_money=self.money, initial_earned=self.earned,
                initial_reputation=self.reputation
            )
            out_events.append(("quan", "phase_start", {}, current_day))

        elif self.phase == "quan" and self.sub_sim.done:
            # Quán kết thúc
            self.money = self.sub_sim.money
            self.earned = self.sub_sim.earned
            self.reputation = self.sub_sim.reputation
            self.stock = dict(self.sub_sim.stock)

            self.phase = "shop"
            shop_scen = dict(self.scenario.get("shop", {}))
            self.sub_sim = ShopSim(
                self.tuning, shop_scen,
                money=self.money, earned=self.earned, reputation=self.reputation,
                stock=self.stock, upgrades=self.upgrades
            )
            out_events.append(("shop", "phase_start", {}, current_day))

        elif self.phase == "shop" and self.sub_sim.done:
            # Shop kết thúc
            self.money = self.sub_sim.money
            self.upgrades = dict(self.sub_sim.upgrades)
            self.days_completed += 1

            if self.days_completed >= self.days:
                self.done = True
                self.reason = "days_complete"
            else:
                self.day += 1
                self._init_day(self.day)
                out_events.append(("gather", "day_start", {}, self.day))
                out_events.append(("gather", "day_plan", dict(self.current_day_plan), self.day))
                out_events.append(("gather", "phase_start", {}, self.day))

        return out_events
