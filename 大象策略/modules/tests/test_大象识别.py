#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大象识别模块的测试文件
"""
import os
import sys
import time
from typing import Dict

# 添加父目录到系统路径，解决导入问题
当前路径 = os.path.dirname(os.path.abspath(__file__))
父目录 = os.path.dirname(当前路径)
项目根目录 = os.path.dirname(父目录)
if 父目录 not in sys.path:
    sys.path.append(父目录)
if 项目根目录 not in sys.path:
    sys.path.append(项目根目录)

# 灵活导入模块
try:
    # 当作为包导入时
    from modules.大象识别 import 大象识别器
    from modules.日志 import get_logger
except ImportError:
    try:
        # 当直接运行时
        from 大象策略.modules.大象识别 import 大象识别器
        from 大象策略.modules.日志 import get_logger
    except ImportError:
        # 相对路径导入
        from ..大象识别 import 大象识别器
        from ..日志 import get_logger

def 测试大象识别() -> Dict:
    """测试大象识别功能"""
    logger = get_logger("测试_大象识别")
    logger.info("开始测试大象识别功能")
    
    # 创建大象识别器实例
    大象识别 = 大象识别器(
        大象委托量阈值=1000000.0,
        大象价差阈值=3,
        确认次数=2,  # 降低确认次数，方便测试
        大象稳定时间=1,  # 降低稳定时间，方便测试
        启用卖单识别=True
    )
    
    # 生成测试盘口数据
    买盘 = [
        (10.0, 1000),  # 价格, 数量
        (9.9, 150000),  # 大象
        (9.8, 1000),
        (9.7, 500)
    ]
    
    卖盘 = [
        (10.1, 1000),
        (10.2, 200000),  # 大象
        (10.3, 1000),
        (10.4, 500)
    ]
    
    当前时间 = int(time.time() * 1000)  # 毫秒时间戳
    
    # 测试买单大象识别
    买单大象 = 大象识别.检测大象("000001", 当前时间, 买盘, 卖盘)
    
    # 等待一下，确保大象稳定时间过去
    time.sleep(1.5)
    
    # 再次检测，验证确认机制
    买单大象 = 大象识别.检测大象("000001", 当前时间 + 1500, 买盘, 卖盘)
    
    # 测试卖单大象识别
    卖单大象 = 大象识别.检测卖单大象("000001", 当前时间, 买盘, 卖盘)
    
    # 等待一下，确保大象稳定时间过去
    time.sleep(1.5)
    
    # 再次检测，验证确认机制
    卖单大象 = 大象识别.检测卖单大象("000001", 当前时间 + 1500, 买盘, 卖盘)
    
    logger.info(f"买单大象检测结果: {买单大象}")
    logger.info(f"卖单大象检测结果: {卖单大象}")
    
    # 验证结果
    测试通过 = 买单大象 is not None and 卖单大象 is not None
    
    # 测试大象跟踪和清理
    大象识别.重置("000001")
    
    # 验证重置是否成功
    买单大象 = 大象识别.检测大象("000001", 当前时间 + 3000, 买盘, 卖盘)
    测试结果 = {
        "成功": 测试通过,
        "买单大象": 买单大象 is not None,
        "卖单大象": 卖单大象 is not None
    }
    
    if 测试通过:
        logger.info("大象识别测试通过")
    else:
        logger.error("大象识别测试失败")
        
    return 测试结果

def 测试大象消失检测():
    """测试大象消失检测功能"""
    logger = get_logger("测试_大象消失检测")
    logger.info("开始测试大象消失检测功能")
    
    # 创建大象识别器实例
    大象识别 = 大象识别器(
        大象委托量阈值=1000000.0,
        大象价差阈值=3,
        确认次数=1,  # 降低确认次数，方便测试
        大象稳定时间=1  # 降低稳定时间，方便测试
    )
    
    # 生成测试盘口数据
    买盘1 = [
        (10.0, 1000), 
        (9.9, 150000),  # 大象
        (9.8, 1000),
        (9.7, 500)
    ]
    
    卖盘1 = [
        (10.1, 1000),
        (10.2, 1000),
        (10.3, 1000)
    ]
    
    当前时间 = int(time.time() * 1000)
    
    # 先识别大象
    大象 = 大象识别.检测大象("000001", 当前时间, 买盘1, 卖盘1)
    
    # 等待确认
    time.sleep(1.5)
    大象 = 大象识别.检测大象("000001", 当前时间 + 1500, 买盘1, 卖盘1)
    
    logger.info(f"已识别大象: {大象}")
    
    # 检查已识别大象的价格
    if not 大象:
        logger.error("大象识别测试失败: 无法找到大象")
        return {"成功": False, "错误": "无法识别大象"}
    
    原大象价格 = 大象["价格"]
    原大象数量 = 大象["数量"]
    原大象位置 = 大象["深度位置"]
    logger.info(f"原大象价格: {原大象价格}, 原大象数量: {原大象数量}, 深度位置: {原大象位置}")
    
    # 模拟大象减少90%数量但仍然在原位置
    买盘2 = list(买盘1)  # 复制原买盘
    买盘2[原大象位置] = (原大象价格, int(原大象数量 * 0.1))  # 减少90%数量
    
    # 模拟大象完全消失（删除原来价格的档位）
    买盘3 = []
    for i, (价格, 数量) in enumerate(买盘1):
        if 价格 != 原大象价格:  # 只保留非大象价格的档位
            买盘3.append((价格, 数量))
    
    # 检查大象是否部分消失（数量减少）
    盘口数据 = {"买盘": 买盘2, "卖盘": 卖盘1}
    大象减少 = 大象识别.检查大象是否消失("000001", 盘口数据, 类型="买单")
    
    # 检查大象是否真正消失（价格不再存在）
    盘口数据 = {"买盘": 买盘3, "卖盘": 卖盘1}
    大象消失 = 大象识别.检查大象是否消失("000001", 盘口数据, 类型="买单")
    
    logger.info(f"大象数量下降检测结果(减少90%): {大象减少}")
    logger.info(f"大象完全消失检测结果(价格不存在): {大象消失}")
    
    # 总的测试结果
    测试结果 = 大象减少 or 大象消失
    if 测试结果:
        logger.info("大象消失检测测试通过")
    else:
        logger.error("大象消失检测测试失败")
    
    return {
        "成功": 测试结果,
        "大象初始识别": 大象 is not None,
        "大象数量下降检测": 大象减少,
        "大象完全消失检测": 大象消失
    }

def 运行所有测试():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行大象识别模块测试")
    print("=" * 50)
    
    # 确保日志配置
    try:
        from 大象策略.modules.日志 import 配置日志
    except ImportError:
        try:
            from modules.日志 import 配置日志
        except ImportError:
            from ..日志 import 配置日志
    
    try:
        配置日志(级别="info")
    except Exception as e:
        print(f"警告: 配置日志系统失败: {e}")
    
    测试结果1 = 测试大象识别()
    print(f"大象识别功能测试结果: {测试结果1}")
    
    测试结果2 = 测试大象消失检测()
    print(f"大象消失检测测试结果: {测试结果2}")
    
    print("=" * 50)
    if 测试结果1.get("成功", False) and 测试结果2.get("成功", False):
        print("所有测试通过!")
    else:
        print("测试失败，请检查日志")
    print("=" * 50)

if __name__ == "__main__":
    运行所有测试() 