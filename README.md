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

- v4（当前主程序）：主干 = 最长单根放水平；分支垂直于上级主干，逐级交替；同点第三根起偏 30°；硬规则 9 项（任一失败不出图），输出规则检查清单。
- v3 / v3-fix：早期版本，留作追溯。

```bash
python3 unfold_2d/unfold_2d_v4.py topology.json -o out_dir
```

输出：DXF（块输出）、Excel、layout.json、checklist_v4.md、comparison_v4.md（v1/v3-fix/v4 对比）。

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
