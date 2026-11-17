# 连接器到连接器全局最长路径分析

本目录是独立算法模块，按当前拓扑数据结构对每一条 segment 建图并计算最长连接器路径。它不会覆盖原有 v3 布局器，也不会把分析结果冒充为已完成的二维主干布局。

## 算法规则
- 节点：topology.json 的 nodes。
- 边：segments 中的每条管段；一个 branch 可以有多条 segment，搜索时逐段保留。
- 权重：segments[].length 的 3D 真实长度，不是 XY 投影长度。
- 目标：两个不同连接器之间的最长简单路径；路径中节点不重复。
- 路径允许经过中间连接器后继续到另一个连接器。
- 自环（na == nb）不能构成简单节点路径，单独列入 ignored_self_loops。
- 输出连接器端点、总长、节点序列、segment/branch 序列、逐段明细和搜索状态数。

## 运行
```bash
python connector_path.py topology.json -o connector_longest_path.json
python -m unittest discover -s tests -v
```

## 样例实测
110 节点、116 segment 样例：CON01 → CON08，约 2341.4 mm，29 条 segment，29 个连续 branch 对象，搜索 99,864 个状态；3 条自环被排除并记录。

## 当前边界
本次提交完成的是最长路径识别与审计。原 v3 布局器当前仍按最长单根 branch 选择水平主干；尚未将全局最长 connector path 接入新的二维骨架布局。下一阶段必须同时处理主路径长度守恒、连接器端点定位、分支挂接与环约束，不能简单把整条路径强制拉成水平线。
