#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大象策略股票行情订阅测试
用于验证_订阅股票行情方法的健壮性
"""
import os
import sys
from datetime import datetime

# 添加当前目录到系统路径，确保可以导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 导入大象策略
from 大象策略 import 大象策略

def 主程序():
    """主程序入口"""
    print("=" * 50)
    print("大象策略股票行情订阅测试")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"当前路径: {os.getcwd()}")
    print("=" * 50)
    
    # 1. 创建策略实例，cta_engine为None
    print("\n1. 创建策略实例，cta_engine为None")
    策略实例 = 大象策略(
        cta_engine=None,
        strategy_name="测试大象策略",
        vt_symbol=None,
        setting=None,
        股票列表=["000001", "600000", "600036"],
        初始资金=1000000.0,
        大象委托量阈值=1000000.0
    )
    
    # 2. 测试直接订阅股票行情
    print("\n2. 测试直接订阅股票行情")
    策略实例._订阅股票行情()
    
    # 3. 创建并订阅自定义股票列表
    print("\n3. 创建并订阅自定义股票列表")
    策略实例.交易股票列表 = ["000333", "000651", "000858"]
    策略实例._订阅股票行情()
    
    # 4. 测试空列表
    print("\n4. 测试空列表")
    策略实例.交易股票列表 = []
    策略实例._订阅股票行情()
    
    # 5. 设置参数管理器中的股票列表
    print("\n5. 设置参数管理器中的股票列表")
    策略实例.参数管理.设置股票列表(["002230", "300059", "600887"])
    策略实例._订阅股票行情()
    
    # 完成测试
    print("\n测试完成")
    print("=" * 50)
    return 策略实例

if __name__ == "__main__":
    try:
        策略实例 = 主程序()
        print("测试成功完成")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        # 打印完整的错误信息
        import traceback
        traceback.print_exc() 