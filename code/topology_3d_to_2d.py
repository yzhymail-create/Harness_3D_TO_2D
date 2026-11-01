#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线束3D拓扑转2D DXF生成器
将3D拓扑数据投影到2D平面，生成CAD可读的DXF文件
"""

import json
import math
import os
from typing import Dict, List, Tuple, Optional
import ezdxf


class Topology3DTo2D:
    """3D拓扑转2D核心类"""
    
    def __init__(self, topology_json_path: str):
        """
        初始化转换器
        
        Args:
            topology_json_path: topology.json文件路径
        """
        self.topology_path = topology_json_path
        self.data = self._load_topology()
        
    def _load_topology(self) -> Dict:
        """加载拓扑数据"""
        with open(self.topology_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _calculate_segment_length(self, p0: List[float], p1: List[float]) -> float:
        """计算线段3D长度"""
        return math.sqrt(
            (p1[0] - p0[0])**2 + 
            (p1[1] - p0[1])**2 + 
            (p1[2] - p0[2])**2
        )
    
    def _project_to_2d(self, point_3d: List[float]) -> Tuple[float, float]:
        """
        3D点投影到2D平面
        
        默认使用XY平面投影（忽略Z坐标）
        
        Args:
            point_3d: [x, y, z] 3D坐标
            
        Returns:
            (x, y) 2D坐标
        """
        return (point_3d[0], point_3d[1])
    
    def _get_node_style(self, node_type: str) -> Tuple[str, float]:
        """
        获取节点样式
        
        Args:
            node_type: 节点类型
            
        Returns:
            (layer_name, radius) 图层名和圆圈半径
        """
        styles = {
            'connector': ('CONNECTORS', 5.0),
            'clamp': ('CLAMPS', 3.0),
            'fork': ('FORKS', 4.0),
            'joint': ('JOINTS', 4.0),
            'hanging': ('HANGING', 3.0),
        }
        return styles.get(node_type, ('TUBES', 2.0))
    
    def create_dxf(
        self,
        output_path: str,
        dxf_version: str = 'R2000',
        show_labels: bool = True,
        show_dimensions: bool = True,
        label_height: float = 3.0
    ) -> Dict[str, int]:
        """
        生成DXF文件
        
        Args:
            output_path: 输出DXF文件路径
            dxf_version: DXF版本（R2000/R2004/R2007/R2010）
            show_labels: 是否显示节点名称标注
            show_dimensions: 是否显示线段长度标注
            label_height: 文字高度
            
        Returns:
            统计信息字典
        """
        # 创建DXF文档
        doc = ezdxf.new(dxf_version)
        msp = doc.modelspace()
        
        # 添加图层
        self._setup_layers(doc)
        
        # 统计信息
        stats = {
            'segments': 0,
            'nodes': 0,
            'labels': 0,
            'dimensions': 0
        }
        
        # 绘制线段
        for seg in self.data['segments']:
            p0 = seg['p0']
            p1 = seg['p1']
            
            # 投影到2D
            p0_2d = self._project_to_2d(p0)
            p1_2d = self._project_to_2d(p1)
            
            # 绘制线段
            msp.add_line(p0_2d, p1_2d, dxfattribs={'layer': 'TUBES'})
            stats['segments'] += 1
            
            # 标注长度
            if show_dimensions:
                length = self._calculate_segment_length(p0, p1)
                mid_x = (p0_2d[0] + p1_2d[0]) / 2
                mid_y = (p0_2d[1] + p1_2d[1]) / 2
                msp.add_text(
                    f"{length:.1f}", 
                    height=label_height,
                    dxfattribs={'layer': 'DIM'}
                ).set_placement((mid_x + 2, mid_y + 2))
                stats['dimensions'] += 1
        
        # 绘制节点
        for node in self.data['nodes']:
            x, y, z = node['xyz']
            code = node['code']
            node_type = node['type']
            
            layer, radius = self._get_node_style(node_type)
            
            # 绘制圆圈
            msp.add_circle((x, y), radius, dxfattribs={'layer': layer})
            stats['nodes'] += 1
            
            # 标注名称
            if show_labels:
                msp.add_text(
                    code, 
                    height=label_height,
                    dxfattribs={'layer': 'TEXT'}
                ).set_placement((x + radius + 1, y + radius + 1))
                stats['labels'] += 1
        
        # 保存文件
        doc.saveas(output_path)
        
        return stats
    
    def _setup_layers(self, doc):
        """设置图层"""
        layers = [
            ('TUBES', 7, '管子线段'),
            ('CONNECTORS', 1, '连接器'),
            ('CLAMPS', 5, '卡扣'),
            ('FORKS', 30, '分支点'),
            ('JOINTS', 4, '接头点'),
            ('HANGING', 6, '悬挂点'),
            ('TEXT', 2, '文字标注'),
            ('DIM', 3, '尺寸标注'),
        ]
        
        for name, color, desc in layers:
            doc.layers.add(name, color=color)
    
    def print_summary(self, stats: Dict[str, int]):
        """打印统计摘要"""
        print(f"\n=== 3D转2D统计 ===")
        print(f"线段: {stats['segments']}条")
        print(f"节点: {stats['nodes']}个")
        print(f"标注: {stats['labels']}个")
        print(f"尺寸: {stats['dimensions']}个")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='线束3D拓扑转2D DXF生成器')
    parser.add_argument('topology_json', help='topology.json文件路径')
    parser.add_argument('-o', '--output', default='topology_2d.dxf', help='输出DXF文件路径')
    parser.add_argument('--version', default='R2000', choices=['R2000', 'R2004', 'R2007', 'R2010'],
                        help='DXF版本（默认：R2000）')
    parser.add_argument('--no-labels', action='store_true', help='不显示节点名称')
    parser.add_argument('--no-dimensions', action='store_true', help='不显示线段长度')
    parser.add_argument('--label-height', type=float, default=3.0, help='文字高度（默认：3.0）')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.topology_json):
        print(f"错误：找不到文件 {args.topology_json}")
        return 1
    
    # 创建转换器
    converter = Topology3DTo2D(args.topology_json)
    
    # 生成DXF
    print(f"正在转换: {args.topology_json}")
    stats = converter.create_dxf(
        output_path=args.output,
        dxf_version=args.version,
        show_labels=not args.no_labels,
        show_dimensions=not args.no_dimensions,
        label_height=args.label_height
    )
    
    # 打印统计
    converter.print_summary(stats)
    
    # 显示文件信息
    file_size = os.path.getsize(args.output) / 1024
    print(f"\n已保存: {args.output}")
    print(f"DXF版本: {args.version}")
    print(f"文件大小: {file_size:.1f} KB")
    
    return 0


if __name__ == '__main__':
    exit(main())
