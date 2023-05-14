#!/usr/bin/env python3
import pandas as pd
from openpyxl import Workbook
from doctor_card import Card

import pickle, pathlib
assignemnts = pickle.load(pathlib.Path("./result.pkl").open('rb'))
assignment_tp_list = [
    (_['doctor'], _['card'].machine, _['card'].formatted_date, ) for _ in assignemnts
]
assignment_tp_list.extend(
    [(_[0], "介入 702" , _[2]) for _ in assignment_tp_list if _[1]=="夜班"]
)

machine_order = [
    "夜班", "门4 DD70", "门3 声科", "门1 Q7", "介入 702",
    "门5", "Q5", "床边", "elite", "701连班", "开立", "介入 s3000", "门3 880"
]


# 将排序机器转换为排序索引
machine_order_index = {machine: index for index, machine in enumerate(machine_order)}

# 所有医生名字的集合
all_doctors = set(doctor for doctor, _, _ in assignment_tp_list)

# 将数据转换为 DataFrame
data = pd.DataFrame(assignment_tp_list, columns=["Doctor", "Machine", "Date"])

# 使用 pivot 将数据转换为适当的格式
pivot_data = data.pivot_table(index="Date", columns="Machine", values="Doctor", aggfunc='first')

# 按照 machine_order 对列进行排序
pivot_data = pivot_data[machine_order]

# 为 DataFrame 添加未出现在当天 assign 阵列中的所有医生并标记为 "休息"
for date in pivot_data.index:
    assigned_doctors = set(pivot_data.loc[date].dropna().values)
    resting_doctors = all_doctors.difference(assigned_doctors)
    pivot_data.loc[date, "Rest"] = ", ".join(sorted(resting_doctors))
weekdays = pivot_data.index.to_series().apply(lambda date_string: date_string.split(" ")[1])
pivot_data.insert(0, "Weekday", weekdays)
# 保存为 Excel
pivot_data.to_excel("assignment_schedule_ordered_machines.xlsx", engine='openpyxl')