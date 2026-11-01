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
