#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大象策略启动脚本
"""

import os
import sys
import argparse
import json

# 添加当前目录到系统路径
当前路径 = os.path.dirname(os.path.abspath(__file__))
if 当前路径 not in sys.path:
    sys.path.append(当前路径)

# 正确导入大象策略类和必要的VNPY组件
from 大象策略 import 大象策略

# 导入VNPY必要组件
try:
    from vnpy.event import EventEngine
    from vnpy.trader.engine import MainEngine
    from vnpy.trader.gateway.ctp import CtpGateway
    # 导入模拟交易网关用于测试
    from vnpy.gateway.tushare import TushareGateway
    from vnpy.gateway.simulator import SimulatorGateway
    from vnpy.app.cta_strategy import CtaStrategyApp
    from vnpy.app.cta_strategy.base import CtaEngine
except ImportError as e:
    print(f"导入VNPY组件错误，请确保已正确安装VNPY: {e}")
    sys.exit(1)

def 连接实盘网关(main_engine):
    """连接实盘CTP网关"""
    # 从配置文件中读取CTP账户信息
    config_path = os.path.join(当前路径, "modules", "config", "ctp_config.json")
    
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                ctp_setting = json.load(f)
        else:
            # 默认配置，需要用户修改
            ctp_setting = {
                "用户名": "",
                "密码": "",
                "经纪商代码": "",
                "交易服务器": "",
                "行情服务器": "",
                "产品名称": "simnow_client_test",
                "授权码": "",
                "产品信息": ""
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(ctp_setting, f, indent=4, ensure_ascii=False)
            print(f"已创建CTP配置文件模板，请修改后重新运行: {config_path}")
            return False
        
        # 检查配置是否完整
        if not ctp_setting["用户名"] or not ctp_setting["密码"]:
            print(f"CTP配置不完整，请修改配置文件后重新运行: {config_path}")
            return False
        
        # 连接CTP
        gateway_name = "CTP"
        main_engine.connect(ctp_setting, gateway_name)
        print(f"已连接到CTP网关: {gateway_name}")
        return True
        
    except Exception as e:
        print(f"连接CTP网关失败: {e}")
        return False

def 连接模拟网关(main_engine):
    """连接模拟网关用于测试"""
    # 连接模拟网关
    gateway_name = "SIMULATOR"
    main_engine.add_gateway(SimulatorGateway)
    main_engine.connect({}, gateway_name)
    print(f"已连接到模拟网关: {gateway_name}")
    return True

def main(模式: str = "模拟"):
    """
    主函数
    
    参数:
        模式: 运行模式，"实盘"或"模拟"
    """
    print(f"启动大象策略 (模式: {模式})...")
    try:
        # 创建事件引擎
        event_engine = EventEngine()
        print("事件引擎已创建")
        
        # 创建主引擎
        main_engine = MainEngine(event_engine)
        print("主引擎已创建")
        
        # 根据模式连接不同的网关
        连接成功 = False
        if 模式 == "实盘":
            # 添加CTP网关
            main_engine.add_gateway(CtpGateway)
            print("已添加CTP网关")
            连接成功 = 连接实盘网关(main_engine)
        else:
            # 添加模拟网关
            连接成功 = 连接模拟网关(main_engine)
        
        if not 连接成功:
            print("网关连接失败，无法启动策略")
            return
        
        # 添加策略应用
        main_engine.add_app(CtaStrategyApp)
        print("已添加CTA策略应用")
        
        # 获取CTA引擎
        cta_engine = main_engine.get_engine(CtaEngine.engine_type)
        if not cta_engine:
            raise ValueError("无法获取CTA策略引擎")
        print("CTA策略引擎已获取")
        
        # 加载策略配置
        config_path = os.path.join(当前路径, "modules", "config", "strategy_config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                strategy_setting = json.load(f)
            print(f"已加载策略配置: {config_path}")
        else:
            strategy_setting = {}
            print("未找到策略配置，使用默认配置")
        
        # 初始化策略实例，传入CTA引擎
        策略实例 = 大象策略(
            cta_engine=cta_engine,
            strategy_name="大象策略",
            vt_symbol="",  # 可根据需要添加默认交易品种
            setting=strategy_setting
        )
        print("策略实例已创建")
        
        # 初始化并启动策略
        策略实例.on_init()
        策略实例.on_start()
        print("大象策略已启动成功！")
        
        # 保持程序运行
        input("按回车键退出...")
        
        # 退出时执行停止
        策略实例.on_stop()
        main_engine.close()
        print("大象策略已停止。")
        
    except Exception as e:
        print(f"启动策略时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="大象策略启动脚本")
    parser.add_argument("-m", "--mode", dest="模式", 
                        choices=["实盘", "模拟"], default="模拟",
                        help="运行模式：实盘 或 模拟")
    
    args = parser.parse_args()
    
    # 运行主函数
    main(args.模式) 