#!/usr/bin/env python3

from datetime import datetime, timedelta
import numpy as np
import math
import pulp

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
        return f"{self.date.month}月{self.date.day}日 星期{weekday_names[(self.date.weekday() % 7) + 1]}"

class Scheduler:
    def __init__(self, start_date_str, end_date_str, machine_names, doctors):
        self.start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        self.machine_names = machine_names
        self.doctors = doctors  # 医生列表的成员变量
        date_list = []
        current_date = self.start_date
        while current_date <= self.end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        all_cards = []
        for date in date_list:
            if date.weekday() in (5, 6):
                machine = "夜班"
                all_cards.append(Card(machine, date, machine_names.index(machine)))
            else:
                for machine in self.machine_names:
                    all_cards.append(Card(machine, date, machine_names.index(machine)))
        for card in all_cards:
            self.fill_exclusion_cards(card, all_cards)
        self.all_cards = all_cards
    
    def calc_assignments_score(self, assignments):
        card_count = {doctor: len([assig for assig in assignments if assig["doctor"] == doctor]) for doctor in self.doctors}
        variance = np.var(list(card_count.values()))
        return variance
    
    def check_assignments(self, assignments):
        valid = True
        
        for doctor in self.doctors:
            doctor_cards = [assig['card'] for assig in assignments if assig['doctor'] == doctor]
            
            for card in doctor_cards:
                for exclusion_card in card.exclusion_cards:
                    if exclusion_card in doctor_cards:
                        # print(f"{doctor} 分配到互斥卡片：{card} 和 {exclusion_card}")
                        valid = False
        return valid
    def debug(self):
        for card in self.all_cards:
            print(card)
            if card.exclusion_cards:
                print("EXCLUSION_CARDS", [_ for _ in card.exclusion_cards])
        print("DOCTOR_LIST: ")
        for doctor in self.doctors:
            print(doctor)

    def fill_exclusion_cards(self, card, all_cards):
        if card.machine == "夜班":
            if card.date.weekday() in range(4):  # 周一到周四的夜班
                next_day = card.date + timedelta(days=1)
                for c in all_cards:
                    if c.date == next_day:
                        card.exclusion_cards.append(c)
            elif card.date.weekday() == 4:  # 周五的夜班
                next_week_monday = card.date + timedelta(days=3)
                for c in all_cards:
                    if c.date == next_week_monday:
                        card.exclusion_cards.append(c)
            elif card.date.weekday() == 5:  # 周六的夜班
                friday = card.date - timedelta(days=1)
                next_tuesday = card.date + timedelta(days=2)
                for c in all_cards:
                    if c.date == friday or c.date == next_tuesday:
                        card.exclusion_cards.append(c)
            elif card.date.weekday() == 6:  # 周日的夜班
                wednesday = card.date - timedelta(days=3)
                next_monday = card.date + timedelta(days=1)
                for c in all_cards:
                    if c.date == wednesday or c.date == next_monday:
                        card.exclusion_cards.append(c)
        recent_one_week_date = [
            card.date + timedelta(days=i+1) for i in range(8)
        ]
        for c in all_cards:
            if c.date in recent_one_week_date and c.machine==card.machine:
                card.exclusion_cards.append(c)
        for c in all_cards:
            if c != card and c.date == card.date:
                card.exclusion_cards.append(c)
        card.exclusion_cards = list(set(card.exclusion_cards))
    def make_assignments(self):
        # 创建问题实例
        problem = pulp.LpProblem("MinimizeVariance", pulp.LpMinimize)

        # 创建变量
        x = {(i, j): pulp.LpVariable(cat=pulp.LpBinary, name=f"x_{i}_{j}") for i, card in enumerate(self.all_cards) for j, doctor in enumerate(self.doctors)}


        # 目标函数: 绝对误差之和 (替代方差最小化)
        mean_card_count = len(self.all_cards) / len(self.doctors)
        abs_error_sum = pulp.lpSum([pulp.lpSum(x[(i, j)] for i, card in enumerate(self.all_cards)) - mean_card_count for j, doctor in enumerate(self.doctors)])
        problem += abs_error_sum
        # 约束条件
        # 1. 每张卡片分配给一个医生
        for i, card in enumerate(self.all_cards):
            problem += pulp.lpSum(x[(i, j)] for j, doctor in enumerate(self.doctors)) == 1
        
        # 2. 互斥约束
        for i, card in enumerate(self.all_cards):
            for j, doctor in enumerate(self.doctors):
                for excluded_card in card.exclusion_cards:
                    k = self.all_cards.index(excluded_card)
                    problem += x[(i, j)] + x[(k, j)] <= 1

        # 求解问题
        problem.solve()

        # 提取解
        assignments = [{"doctor": self.doctors[j], "card": self.all_cards[i]} for i, card in enumerate(self.all_cards) for j, doctor in enumerate(self.doctors) if x[(i, j)].value() == 1]
        return assignments

# 输入数据
start_date_str = "2023-06-01"
end_date_str = "2023-06-30"
machine_names = [
    "夜班", "门4 DD70", "门3 声科", "门1 Q7", "介入 702",
    "门5", "Q5", "床边", "elite", "701连班", "开立", "介入 s3000", "门3 880"
]
machine_names = [
    "夜班", 
    "门4 DD70", 
    "门3 声科", 
    "门1 Q7", 
    # "介入 702", 
    "门5", 
    "Q5", 
    "床边", 
    "elite",
    "701连班", 
    "开立", 
    "介入 s3000", 
    # "门3 880"
]
doctor_list = ['谭', '马', '储', '齐', '晶', '孙', '鲍', '月', '郭', '娜', '婷', '爽', '王', '陈']

scheduler = Scheduler(start_date_str, end_date_str, machine_names, doctor_list)
# scheduler.debug()

assignments = scheduler.make_assignments()

# for assignment in sorted(assignments, key=lambda x: (x['card'].date, x['card'].machine_idx)):
#     print(assignment)

# for assignment in sorted(assignments, key=lambda x: (x['doctor'], x['card'].date)):
#     print(assignment)
import pickle, pathlib
pickle.dump(assignments, pathlib.Path("./result.pkl").open('wb'))
