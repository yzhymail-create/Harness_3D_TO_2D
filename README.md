# 线束3D拓扑转2D DXF生成器

将线束3D拓扑数据（topology.json）转换为2D DXF文件，用于CAD查看和打印。

## 功能特性

- ✅ 3D→2D投影（XY平面）
- ✅ 图层管理（管子、连接器、卡扣等）
- ✅ 自动标注（节点名称、线段长度）
- ✅ 多版本DXF支持（R2000/R2004/R2007/R2010）
- ✅ 批量转换工具
- ✅ CAD兼容（AutoCAD、中望CAD、浩辰CAD）

## 快速开始

### 安装依赖

```bash
pip install ezdxf
```

### 单文件转换

```bash
python code/topology_3d_to_2d.py topology.json -o output.dxf
```

### 批量转换

```bash
python code/batch_convert.py input_dir output_dir
```

## 树形展开路线（unfold_2d/）

另一条展开路线：按主干—分支层级把 3D 拓扑摊平，长度 1:1、拓扑不变。需求与规则见 [unfold_2d/需求说明.md](unfold_2d/需求说明.md)。

- v6p2（当前主流程）：v6p1 布局 + `merge_joints_v6p2.py` 后处理：§十六过路点合并（IP：19 个点，13 条合并路径，路径 108→91、节点 110→91，几何不动）＋自环改小圆环（3 处，不按 1:1，真值在弹窗）＋线色统一深蓝＋标签下拉菜单。IP 实测：X 交叉 0 对，查看器实测全过。
- v6p1：v6 + §十五平行对只画一根（4 对各留走主干/脊线那根；打折画法作废）。
- v6：§十四分支逐层最长路径（脊线分解 31 条，整条拉直垂直于上级脊线；先算后画）；主干 = 最长连接器—连接器路径整条拉直水平；硬规则 10 项（任一失败不出图），输出规则检查清单。IP 实测：X 交叉 0 对；H1 竖向居中 14.45% 由用户 2026-11-17 决定豁免通过（名义阈值仍 5%）。
- v5：主干改最长连接器—连接器路径整条拉直；X 交叉 11 对。
- v4：主干 = 最长单根（定义已作废，留作追溯）。
- v3 / v3-fix：早期版本，留作追溯。

```bash
python3 unfold_2d/unfold_2d_v6p1.py topology.json -o out_dir
python3 unfold_2d/merge_joints_v6p2.py out_dir/layout.json topology.json out_dir_v6p2
python3 unfold_2d/make_viewer.py out_dir_v6p2/layout.json viewer.html
```

输出：DXF（块输出）、Excel、layout.json、plan.json、checklist_v6p1.md、branch_layers.md、合并后 layout.json、merge_report_v6p2.md、单文件网页查看器。

## 输出示例

生成的DXF文件包含：

- **531条管子线段**（灰色）
- **105个连接器**（红色圆圈）
- **173个卡扣**（蓝色圆圈）
- **95个分支点**（橙色圆圈）
- **67个接头点**（青色圆圈）
- **31个悬挂点**（紫色圆圈）
- **节点名称标注**（黄色文字）
- **线段长度标注**（绿色文字）

## 图层说明

| 图层 | 颜色 | 内容 |
|------|------|------|
| TUBES | 白/灰 | 管子线段 |
| CONNECTORS | 红 | 连接器 |
| CLAMPS | 蓝 | 卡扣 |
| FORKS | 橙 | 分支点 |
| JOINTS | 青 | 接头点 |
| HANGING | 紫 | 悬挂点 |
| TEXT | 黄 | 节点名称 |
| DIM | 绿 | 线段长度 |

## 命令行选项

```bash
python topology_3d_to_2d.py topology.json [选项]

选项：
  -o, --output PATH       输出文件路径（默认：topology_2d.dxf）
  --version VERSION       DXF版本（R2000/R2004/R2007/R2010）
  --no-labels             不显示节点名称
  --no-dimensions         不显示线段长度
  --label-height HEIGHT   文字高度（默认：3.0）
```

## 文档

详细文档请查看 [SKILL.md](SKILL.md)

## 许可证

MIT License
