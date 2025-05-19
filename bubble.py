import pandas as pd
import numpy as np
import plotly.express as px
import mysql.connector
import  os
from pathlib import Path
import kaleido

# 生成示例数据
connection = mysql.connector.connect(
        host='sh-cdb-aale09ms.sql.tencentcdb.com',
        user='root',
        port=26059,
        password='Sail@001',
        database='Time_Series'
    )

cursor = connection.cursor()
            # 查询表结构
cursor.execute(f"DESCRIBE daily_data")
            # 获取所有列信息
columns = cursor.fetchall()
            # 提取第一列（列名）
column_names = [column[0] for column in columns]
column_test_name = column_names[1:5]
latest_data = {}
last_data = {}
for col in column_test_name:
    # 查询该列第一个非零值（将TEXT转换为DECIMAL进行比较）
    cursor.execute(f"""
                    SELECT {col} 
                    FROM daily_data
                    WHERE CAST({col} AS DECIMAL) != 0
                    ORDER BY date DESC 
                    LIMIT 1
                """)
    non_zero_value = cursor.fetchone()

    if non_zero_value:
        latest_data[col] = float(non_zero_value[0])
    else:
        latest_data[col] = None  # 如果列中所有值都是0或NULL

for col in column_test_name:
    # 查询该列第一个非零值（将TEXT转换为DECIMAL进行比较）
    cursor.execute(f"""
                    SELECT {col} 
                    FROM daily_data
                    WHERE CAST({col} AS DECIMAL) != 0 
                    ORDER BY date DESC
                    LIMIT 1 offset 1
                """)
    second_non_zero_value = cursor.fetchone()
    if second_non_zero_value:
        last_data[col] = float(second_non_zero_value[0])
    else:
        last_data[col] = None

# 计算增长率
rate = {}
for col in column_test_name:
    if latest_data[col] is not None and last_data[col] is not None and last_data[col] != 0:
        rate[col] = (latest_data[col] / last_data[col]) - 1
    else:
        rate[col] = None  # 标记无法计算的情况

connection.close()
# 生成示例数据
np.random.seed(42)
data = pd.DataFrame({
    'name': column_test_name,
    'value': list(latest_data.values()),  # 数值决定矩形大小
    'weight': [1,1,1,1], # 历史数据
    'rate':list(rate.values())
})
print(data)

# 创建分类列（3个等级）
data['rate_category'] = pd.cut(
    data['rate'],
    bins=[-np.inf, -0.00001, 0.00001, np.inf],  # 边界划分
    labels=['<0', '=0', '>0'],               # 分类标签
    right=False
)

# 自定义颜色映射
color_discrete_map = {
    '>0': 'rgb(226, 17, 0)',  # 正增长-红色
    '<0': 'rgb(29, 191, 151)',  # 负增长-绿色
    '=0': 'rgb(252, 157, 154)' # 零增长-粉色
}

fig = px.treemap(
    data,
    path=['name'],  # 层次结构：先按category分组，再显示name
    values='weight',             # 矩形大小映射到weight
    color='rate_category',              # 颜色映射到weight
    color_discrete_map=color_discrete_map,
    hover_data={
        'name': True,
        'value': ':.1f',
        'rate': ':.2%',  # 显示为百分比格式
        'weight': True
    }
)

# 更新文本显示
fig.update_traces(
    texttemplate='<b>%{label}</b><br>值: %{customdata[1]:.1f}<br>增长率: %{customdata[2]:.2%}',
    textposition='middle center',
    textfont=dict(
        size=16,
        color='white',
        family='Arial'
    ),

    hovertemplate='<b>%{label}</b><br>当前值: %{customdata[1]:.1f}<br>增长率: %{customdata[2]:.2%}<br>权重: %{customdata[3]}<extra></extra>'
)

# 更新布局
fig.update_layout(
    width=800,
    height=600,
    title_font=dict(size=24, color='darkblue', family='Arial Black'),
    uniformtext=dict(
        minsize=12,
        mode='hide',
    ),
    margin=dict(t=50, l=25, r=25, b=25)
)

fig.show()
# 1. 确保桌面路径正确（跨平台兼容）
# desktop_path = str(Path.home() / "Desktop")  # Windows/macOS通用获取桌面路径
# output_file = os.path.join(desktop_path, "test.png")
# print(os.path.exists(desktop_path))
# # 2. 保存图像（需要安装orca或kaleido）
# fig.write_image(output_file,
#                 engine="kaleido",  # 推荐使用kaleido引擎
#                 width=800,         # 保持与布局一致的宽度
#                 height=600,        # 保持与布局一致的高度
#                 scale=2)           # 2倍缩放提高清晰度
#
# print(f"图表已保存至: {output_file}")