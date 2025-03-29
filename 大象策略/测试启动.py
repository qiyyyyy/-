#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大象策略启动测试脚本
用于测试策略启动流程，特别是在CTA引擎未初始化时的健壮性
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
    print("大象策略启动测试")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"当前路径: {os.getcwd()}")
    print("=" * 50)
    
    # 创建策略实例，故意不传入cta_engine
    策略实例 = 大象策略(
        cta_engine=None,
        strategy_name="测试大象策略",
        vt_symbol=None,
        setting=None,
        股票列表=["000001", "600000", "600036"],
        初始资金=1000000.0,
        大象委托量阈值=1000000.0
    )
    
    print("策略实例创建成功，开始初始化...")
    
    # 调用策略初始化方法
    策略实例.on_init()
    
    print("策略初始化完成，尝试订阅行情...")
    
    # 测试更新交易股票列表
    策略实例._更新交易股票列表()
    
    print("更新股票列表完成，测试记录日志...")
    
    # 测试日志记录
    策略实例.write_log("这是一条测试日志")
    
    print("日志记录完成，测试启动策略...")
    
    # 调用策略启动方法
    策略实例.on_start()
    
    print("策略启动完成，测试结束")
    print("=" * 50)
    
    # 返回策略实例以便后续测试
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