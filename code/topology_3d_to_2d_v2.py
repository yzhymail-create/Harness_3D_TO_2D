#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线束3D拓扑转2D DXF生成器 v2.0
使用CAD块（Block）和属性定义，生成专业工程图纸
"""

import json
import math
import os
from typing import Dict, List, Tuple
import ezdxf
from ezdxf.enums import TextEntityAlignment


class Topology3DTo2D_v2:
    """3D拓扑转2D核心类（使用CAD块）"""
    
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
        """3D点投影到2D平面（XY平面）"""
        return (point_3d[0], point_3d[1])
    
    def _create_blocks(self, doc):
        """
        创建CAD块定义
        
        块类型：
        - CONNECTOR_BLOCK: 连接器（红色圆圈 + 属性）
        - CLAMP_BLOCK: 卡扣（蓝色圆圈 + 属性）
        - FORK_BLOCK: 分支点（橙色圆圈 + 属性）
        - JOINT_BLOCK: 接头点（青色圆圈 + 属性）
        - HANGING_BLOCK: 悬挂点（紫色圆圈 + 属性）
        """
        
        # 连接器块
        block = doc.blocks.new(name='CONNECTOR_BLOCK')
        block.add_circle((0, 0), 5, dxfattribs={'color': 1})  # 红色圆圈
        # 添加属性定义
        attdefs = block.add_attdef(
            'NAME', (0, 8), '连接器名称', 
            height=3, color=2
        )
        
        # 卡扣块
        block = doc.blocks.new(name='CLAMP_BLOCK')
        block.add_circle((0, 0), 3, dxfattribs={'color': 5})  # 蓝色圆圈
        block.add_attdef('NAME', (0, 5), '卡扣名称', height=3, color=2)
        
        # 分支点块
        block = doc.blocks.new(name='FORK_BLOCK')
        block.add_circle((0, 0), 4, dxfattribs={'color': 30})  # 橙色圆圈
        block.add_attdef('NAME', (0, 6), '分支点名称', height=3, color=2)
        
        # 接头点块
        block = doc.blocks.new(name='JOINT_BLOCK')
        block.add_circle((0, 0), 4, dxfattribs={'color': 4})  # 青色圆圈
        block.add_attdef('NAME', (0, 6), '接头点名称', height=3, color=2)
        
        # 悬挂点块
        block = doc.blocks.new(name='HANGING_BLOCK')
        block.add_circle((0, 0), 3, dxfattribs={'color': 6})  # 紫色圆圈
        block.add_attdef('NAME', (0, 5), '悬挂点名称', height=3, color=2)
    
    def _get_block_name(self, node_type: str) -> str:
        """根据节点类型获取块名称"""
        block_map = {
            'connector': 'CONNECTOR_BLOCK',
            'clamp': 'CLAMP_BLOCK',
            'fork': 'FORK_BLOCK',
            'joint': 'JOINT_BLOCK',
            'hanging': 'HANGING_BLOCK',
        }
        return block_map.get(node_type, '')
    
    def create_dxf(
        self,
        output_path: str,
        dxf_version: str = 'R2000',
        show_labels: bool = True,
        show_dimensions: bool = True,
        label_height: float = 3.0
    ) -> Dict[str, int]:
        """
        生成DXF文件（使用CAD块）
        
        Args:
            output_path: 输出DXF文件路径
            dxf_version: DXF版本
            show_labels: 是否显示节点名称
            show_dimensions: 是否显示线段长度
            label_height: 文字高度
            
        Returns:
            统计信息字典
        """
        # 创建DXF文档
        doc = ezdxf.new(dxf_version)
        msp = doc.modelspace()
        
        # 设置图层
        self._setup_layers(doc)
        
        # 创建块定义
        self._create_blocks(doc)
        
        # 统计信息
        stats = {
            'segments': 0,
            'nodes': 0,
            'blocks': 0,
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
                
                # 使用带背景的文字，避免重叠
                msp.add_text(
                    f"{length:.1f}", 
                    height=label_height,
                    dxfattribs={'layer': 'DIM', 'color': 3}
                ).set_placement((mid_x + 2, mid_y + 2))
                stats['dimensions'] += 1
        
        # 插入块（节点）
        for node in self.data['nodes']:
            x, y, z = node['xyz']
            code = node['code']
            node_type = node['type']
            
            block_name = self._get_block_name(node_type)
            if not block_name:
                continue
            
            # 插入块
            block_ref = msp.add_blockref(
                block_name, 
                (x, y),
                dxfattribs={'layer': 'NODES'}
            )
            stats['nodes'] += 1
            
            # 添加属性
            if show_labels:
                block_ref.add_attrib(
                    'NAME', code, (0, 0),
                    height=label_height,
                    color=2
                )
                stats['blocks'] += 1
        
        # 保存文件
        doc.saveas(output_path)
        
        return stats
    
    def _setup_layers(self, doc):
        """设置图层"""
        layers = [
            ('TUBES', 7, '管子线段'),
            ('NODES', 1, '节点块'),
            ('TEXT', 2, '文字标注'),
            ('DIM', 3, '尺寸标注'),
        ]
        
        for name, color, desc in layers:
            doc.layers.add(name, color=color)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='线束3D拓扑转2D DXF生成器 v2.0（使用CAD块）')
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
    converter = Topology3DTo2D_v2(args.topology_json)
    
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
    print(f"\n=== 3D转2D统计 v2.0 ===")
    print(f"线段: {stats['segments']}条")
    print(f"节点: {stats['nodes']}个")
    print(f"块引用: {stats['blocks']}个")
    print(f"尺寸标注: {stats['dimensions']}个")
    
    # 显示文件信息
    file_size = os.path.getsize(args.output) / 1024
    print(f"\n已保存: {args.output}")
    print(f"DXF版本: {args.version}")
    print(f"文件大小: {file_size:.1f} KB")
    
    return 0


if __name__ == '__main__':
    exit(main())
