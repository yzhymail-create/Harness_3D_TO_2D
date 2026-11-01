# 线束3D拓扑转2D DXF生成器 SKILL

## 概述

本SKILL提供将线束3D拓扑数据（topology.json）转换为2D DXF文件的能力，用于CAD查看和打印。

## 核心能力

- **3D→2D投影**：将3D坐标投影到XY平面
- **图层管理**：按实体类型分层（管子、连接器、卡扣等）
- **标注系统**：自动标注节点名称和线段长度
- **多版本支持**：支持R2000/R2004/R2007/R2010 DXF版本
- **批量转换**：支持批量处理多个topology.json文件

## 文件结构

```
harness-3d-to-2d/
├── code/
│   ├── topology_3d_to_2d.py    # 核心转换类
│   └── batch_convert.py        # 批量转换工具
├── requirements.txt            # Python依赖
├── README.md                   # 使用说明
└── SKILL.md                    # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install ezdxf
```

### 2. 单个文件转换

```bash
python code/topology_3d_to_2d.py topology.json -o output.dxf
```

### 3. 批量转换

```bash
python code/batch_convert.py input_dir output_dir
```

## 核心类：Topology3DTo2D

### 初始化

```python
from topology_3d_to_2d import Topology3DTo2D

converter = Topology3DTo2D('topology.json')
```

### 生成DXF

```python
stats = converter.create_dxf(
    output_path='output.dxf',
    dxf_version='R2000',      # DXF版本
    show_labels=True,         # 显示节点名称
    show_dimensions=True,     # 显示线段长度
    label_height=3.0          # 文字高度
)
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output_path` | str | - | 输出DXF文件路径 |
| `dxf_version` | str | 'R2000' | DXF版本（R2000/R2004/R2007/R2010） |
| `show_labels` | bool | True | 是否显示节点名称标注 |
| `show_dimensions` | bool | True | 是否显示线段长度标注 |
| `label_height` | float | 3.0 | 文字高度（mm） |

### 返回值

返回统计信息字典：

```python
{
    'segments': 531,      # 线段数
    'nodes': 471,         # 节点数
    'labels': 471,        # 标注数
    'dimensions': 531     # 尺寸标注数
}
```

## 图层说明

| 图层名 | 颜色 | 内容 | 说明 |
|--------|------|------|------|
| TUBES | 7（白/灰） | 管子线段 | 所有管状分支 |
| CONNECTORS | 1（红） | 连接器圆圈 | 插头类实体 |
| CLAMPS | 5（蓝） | 卡扣圆圈 | 固定卡类实体 |
| FORKS | 30（橙） | 分支点圆圈 | 分支节点 |
| JOINTS | 4（青） | 接头点圆圈 | 接头节点 |
| HANGING | 6（紫） | 悬挂点圆圈 | 悬挂节点 |
| TEXT | 2（黄） | 节点名称 | 文字标注 |
| DIM | 3（绿） | 线段长度 | 尺寸标注 |

## 投影方法

### 默认投影：XY平面

```python
def _project_to_2d(self, point_3d):
    """3D点投影到2D平面（XY平面）"""
    return (point_3d[0], point_3d[1])
```

**特点**：
- 简单直接，保留X/Y坐标
- 忽略Z坐标（高度信息）
- 适合俯视视角查看

### 扩展：其他投影方式

如需其他投影方式，可继承并覆盖`_project_to_2d`方法：

```python
class XZProjection(Topology3DTo2D):
    def _project_to_2d(self, point_3d):
        """XZ平面投影（侧视图）"""
        return (point_3d[0], point_3d[2])

class IsometricProjection(Topology3DTo2D):
    def _project_to_2d(self, point_3d):
        """等轴测投影"""
        x, y, z = point_3d
        return (x - y * 0.5, z + y * 0.866)
```

## 命令行参数

### 单文件转换

```bash
python topology_3d_to_2d.py topology.json [选项]

选项：
  -o, --output PATH       输出文件路径（默认：topology_2d.dxf）
  --version VERSION       DXF版本（R2000/R2004/R2007/R2010，默认：R2000）
  --no-labels             不显示节点名称
  --no-dimensions         不显示线段长度
  --label-height HEIGHT   文字高度（默认：3.0）
```

### 批量转换

```bash
python batch_convert.py input_dir output_dir [选项]

选项：
  --version VERSION       DXF版本（默认：R2000）
  --pattern PATTERN       文件名匹配模式（默认：topology.json）
```

## 常见用法

### 1. 基础转换

```bash
python topology_3d_to_2d.py topology.json -o output.dxf
```

### 2. 仅显示管子，不显示标注

```bash
python topology_3d_to_2d.py topology.json --no-labels --no-dimensions
```

### 3. 使用R2007版本（兼容性更好）

```bash
python topology_3d_to_2d.py topology.json --version R2007
```

### 4. 调整文字大小

```bash
python topology_3d_to_2d.py topology.json --label-height 5.0
```

### 5. 批量转换整个目录

```bash
python batch_convert.py ./harness_data ./dxf_output
```

## 与CAD软件兼容性

| CAD软件 | 推荐DXF版本 | 说明 |
|---------|-------------|------|
| AutoCAD 2000+ | R2000 | 最通用 |
| AutoCAD 2004+ | R2004 | 支持多行文字 |
| AutoCAD 2007+ | R2007 | 支持Unicode |
| AutoCAD 2010+ | R2010 | 最新版本 |
| 中望CAD | R2000 | 兼容性最好 |
| 浩辰CAD | R2000 | 兼容性最好 |

**注意**：
- R2000兼容性最好，推荐默认使用
- 如遇"未知版本"错误，降低版本（R2000 → R2004 → R2007）
- 中文标注建议使用R2007+版本

## 性能指标

| 数据规模 | 转换时间 | 文件大小 |
|---------|---------|---------|
| 100线段/100节点 | <0.1秒 | ~30 KB |
| 500线段/500节点 | ~0.3秒 | ~150 KB |
| 1000线段/1000节点 | ~0.6秒 | ~300 KB |
| 5000线段/5000节点 | ~3秒 | ~1.5 MB |

## 故障排查

### 问题1：CAD打开报错"未知版本"

**原因**：DXF版本太高
**解决**：使用`--version R2000`降低版本

### 问题2：中文标注显示乱码

**原因**：DXF版本不支持Unicode
**解决**：使用`--version R2007`或更高版本

### 问题3：标注文字太小/太大

**原因**：文字高度不合适
**解决**：使用`--label-height`调整（推荐2.0-5.0）

### 问题4：线段交叉严重

**原因**：XY投影导致重叠
**解决**：需要实现更智能的展平算法（树状展开）

## 扩展开发

### 添加新的投影方式

```python
class CustomProjection(Topology3DTo2D):
    def _project_to_2d(self, point_3d):
        # 自定义投影逻辑
        x, y, z = point_3d
        # ... 你的投影算法 ...
        return (new_x, new_y)
```

### 添加新的节点类型

修改`_get_node_style`方法：

```python
def _get_node_style(self, node_type):
    styles = {
        'connector': ('CONNECTORS', 5.0),
        'clamp': ('CLAMPS', 3.0),
        'fork': ('FORKS', 4.0),
        'joint': ('JOINTS', 4.0),
        'hanging': ('HANGING', 3.0),
        'custom_type': ('CUSTOM_LAYER', 4.0),  # 添加新类型
    }
    return styles.get(node_type, ('TUBES', 2.0))
```

### 添加自定义标注

```python
# 在create_dxf方法中添加自定义标注逻辑
for node in self.data['nodes']:
    # ... 绘制节点 ...
    
    # 添加自定义标注
    if node['type'] == 'connector':
        msp.add_text(
            f"连接器: {node['code']}",
            height=label_height,
            dxfattribs={'layer': 'TEXT'}
        ).set_placement((x + 10, y))
```

## 依赖

- Python 3.7+
- ezdxf >= 0.17.0

## 版本历史

- **v1.0** (2026-11-01): 初始版本
  - 支持XY平面投影
  - 支持8种图层
  - 支持节点名称和线段长度标注
  - 支持R2000/R2004/R2007/R2010版本
  - 支持批量转换

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系开发团队。
