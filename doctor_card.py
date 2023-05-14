#!/usr/bin/env python3
class Card:
    def __init__(self, machine, date, machine_idx):
        self.machine = machine
        self.date = date
        self.machine_idx = machine_idx
        self.exclusion_cards = []  # 排斥的 card 列表：对于归属于同一个Doctor的cards，以card_1和card_2为例表示两两关系，不允许card_1的exclusion_cards中包括card_2

    def __repr__(self):
        machine_name=self.machine.replace("夜班", "----夜班")
        if self.date.weekday in (5, 6):
            return f"{machine_name}: 24小时{self.formatted_date}"
        else:
            return f"{machine_name}: {self.formatted_date}"

    @property
    def formatted_date(self):
        weekday_names = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "日"}
        return f"{self.date.month:02}月{self.date.day:02}日 星期{weekday_names[(self.date.weekday() % 7) + 1]}"
