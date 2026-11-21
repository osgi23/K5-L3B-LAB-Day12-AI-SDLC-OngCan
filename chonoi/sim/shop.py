"""Cửa hàng nâng cấp cuối ngày (`shop`, v1.1).

Sau khi đóng quán, Út Sen ghé tiệm tạp hóa mua đồ cho ngày hôm sau.
Lệnh mua hợp lệ qua input buy: 'oxygen', 'hp'.
Kết thúc shop bằng nút shop_done (O) hoặc timeout sau 10 s (600 tick).
"""


class ShopSim:
    mode = "day"
    phase = "shop"

    def __init__(self, tuning, scenario=None, money=0, earned=0, reputation=3.0, stock=None, upgrades=None):
        self.tuning = tuning
        scenario = scenario or {}
        shop_cfg = tuning.get("shop", {})
        self.max_ticks = int(shop_cfg.get("max_ticks", 600))
        self.time_left_ticks = scenario.get("time_left_ticks", self.max_ticks)
        self.money = money
        self.earned = earned
        self.reputation = reputation
        self.stock = dict(stock or {})
        self.upgrades = dict(upgrades or {"oxygen": 0, "hp": 0})
        self.bought_today = set()
        self.phase_tick = 0
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        return {
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0}
        }

    def step(self, inp):
        events = []
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)

        # 1. Xử lý buy (nếu có)
        if inp.buy:
            action = inp.buy
            upgrades_cfg = self.tuning.get("shop", {}).get("upgrades", {})
            if action not in upgrades_cfg:
                events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            else:
                current_level = self.upgrades.get(action, 0)
                available_levels = upgrades_cfg[action]
                if action in self.bought_today or current_level >= len(available_levels):
                    events.append(("buy_failed", {"action": action, "reason": "max_level"}))
                else:
                    target_level = current_level + 1
                    target_info = next((u for u in available_levels if u["level"] == target_level), None)
                    if not target_info:
                        events.append(("buy_failed", {"action": action, "reason": "max_level"}))
                    elif self.money < target_info["price"]:
                        events.append(("buy_failed", {"action": action, "reason": "funds"}))
                    else:
                        price = target_info["price"]
                        self.money -= price
                        self.upgrades[action] = target_level
                        self.bought_today.add(action)
                        events.append(("bought", {
                            "upgrade": action,
                            "level": target_level,
                            "price": price,
                            "money": self.money
                        }))

        # 2. Xử lý shop_done hoặc hết giờ
        if inp.pressed("shop_done"):
            self.done = True
            self.reason = "done"
            events.append(("shop_end", {"reason": "done"}))
        elif self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("shop_end", {"reason": "time"}))

        return events
