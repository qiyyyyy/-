#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行测试脚本 - 启动大象策略测试
"""
import os
import sys
import argparse
import traceback
from typing import Dict, Optional

print("开始执行测试脚本")
print(f"当前路径: {os.getcwd()}")
print(f"系统路径: {sys.path}")

# 添加当前目录到系统路径
当前路径 = os.path.dirname(os.path.abspath(__file__))
if 当前路径 not in sys.path:
    sys.path.append(当前路径)
    print(f"已添加当前路径到系统路径: {当前路径}")

# 尝试导入测试模块
try:
    from modules.测试模块 import 运行所有测试
    print("成功导入测试模块")
except ImportError as e:
    print(f"导入测试模块出错: {e}")
    print("详细错误信息:")
    traceback.print_exc()
    sys.exit(1)

# 尝试导入日志模块
try:
    from modules.日志 import 配置日志
    配置日志(级别="info")
    print("成功配置日志系统")
except ImportError as e:
    print(f"导入日志模块出错: {e}")
    print("详细错误信息:")
    traceback.print_exc()
    # 继续执行，不影响测试

def 启动测试(模块名: Optional[str] = None) -> Dict:
    """
    启动测试
    
    参数:
        模块名: 指定要测试的模块，如果为None则测试所有模块
        
    返回:
        测试结果
    """
    print("=" * 50)
    print(f"开始运行{'指定模块' if 模块名 else '所有模块'}测试")
    print("=" * 50)
    
    try:
        if 模块名:
            # 这里可以添加针对特定模块的测试逻辑
            print(f"测试模块: {模块名}")
            # 例如可以创建测试管理器并只运行指定模块测试
            from modules.测试模块 import 测试管理器
            测试器 = 测试管理器()
            
            if 模块名 == "大象识别":
                try:
                    from modules.tests.test_大象识别 import 测试大象识别, 测试大象消失检测
                    测试器.添加测试("大象识别", lambda _: 测试大象识别(), "测试大象识别功能")
                    测试器.添加测试("大象消失检测", lambda _: 测试大象消失检测(), "测试大象消失检测功能")
                except ImportError as e:
                    print(f"导入大象识别测试模块出错: {e}")
                    traceback.print_exc()
                    return {"错误": f"导入大象识别测试模块出错: {e}"}
            elif 模块名 == "风险控制":
                try:
                    from modules.tests.test_风险控制 import 测试风险控制, 测试资金风险控制
                    测试器.添加测试("风险控制", lambda _: 测试风险控制(), "测试风险控制功能")
                    测试器.添加测试("资金风险控制", lambda _: 测试资金风险控制(), "测试资金风险控制功能")
                except ImportError as e:
                    print(f"导入风险控制测试模块出错: {e}")
                    traceback.print_exc()
                    return {"错误": f"导入风险控制测试模块出错: {e}"}
            else:
                print(f"未知模块: {模块名}")
                return {"错误": f"未知模块: {模块名}"}
                
            结果 = 测试器.运行测试()
            报告 = 测试器.生成测试报告()
            print("\n" + 报告)
            return 结果
        else:
            # 运行所有测试
            return 运行所有测试()
    except Exception as e:
        print(f"测试执行出错: {e}")
        traceback.print_exc()
        return {"错误": f"测试执行出错: {e}"}

if __name__ == "__main__":
    # 解析命令行参数
    解析器 = argparse.ArgumentParser(description="大象策略测试启动脚本")
    解析器.add_argument("-m", "--模块", help="指定要测试的模块，如大象识别、风险控制等")
    参数 = 解析器.parse_args()
    
    try:
        # 运行测试
        启动测试(参数.模块)
    except Exception as e:
        print(f"程序执行出错: {e}")
        traceback.print_exc() 