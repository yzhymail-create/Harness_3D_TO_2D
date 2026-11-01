#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量转换工具
将多个topology.json文件批量转换为DXF
"""

import os
import glob
from topology_3d_to_2d import Topology3DTo2D


def batch_convert(
    input_dir: str,
    output_dir: str,
    dxf_version: str = 'R2000',
    pattern: str = 'topology.json'
) -> int:
    """
    批量转换topology.json为DXF
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        dxf_version: DXF版本
        pattern: 文件名匹配模式
        
    Returns:
        成功转换的文件数
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找所有topology.json文件
    search_pattern = os.path.join(input_dir, '**', pattern)
    files = glob.glob(search_pattern, recursive=True)
    
    if not files:
        print(f"未找到匹配的文件: {search_pattern}")
        return 0
    
    print(f"找到 {len(files)} 个文件")
    
    success_count = 0
    
    for i, json_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] 处理: {json_path}")
        
        try:
            # 生成输出文件名
            rel_path = os.path.relpath(json_path, input_dir)
            parent_dir = os.path.dirname(rel_path)
            output_name = f"{parent_dir or 'output'}_2d.dxf"
            output_path = os.path.join(output_dir, output_name)
            
            # 转换
            converter = Topology3DTo2D(json_path)
            stats = converter.create_dxf(
                output_path=output_path,
                dxf_version=dxf_version
            )
            
            converter.print_summary(stats)
            print(f"✓ 成功: {output_path}")
            success_count += 1
            
        except Exception as e:
            print(f"✗ 失败: {e}")
    
    print(f"\n=== 批量转换完成 ===")
    print(f"成功: {success_count}/{len(files)}")
    
    return success_count


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量转换topology.json为DXF')
    parser.add_argument('input_dir', help='输入目录')
    parser.add_argument('output_dir', help='输出目录')
    parser.add_argument('--version', default='R2000', help='DXF版本')
    parser.add_argument('--pattern', default='topology.json', help='文件名匹配模式')
    
    args = parser.parse_args()
    
    batch_convert(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        dxf_version=args.version,
        pattern=args.pattern
    )


if __name__ == '__main__':
    main()
