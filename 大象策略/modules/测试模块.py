#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试模块 - 检查所有模块是否有bug
"""
import os
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# 导入策略模块
from .资金管理 import 资金管理器
from .大象识别 import 大象识别器
from .交易执行 import 交易执行器
from .风险控制 import 风险控制器
from .网页管理 import 网页管理器


class 测试管理器:
    """测试管理器，管理所有单元测试"""
    
    def __init__(self):
        """初始化测试管理器"""
        self.测试套件 = unittest.TestSuite()
        self.测试结果 = {}
        self.错误信息 = {}
    
    def 添加测试类(self, 测试类):
        """添加测试类到测试套件"""
        测试加载器 = unittest.TestLoader()
        测试 = 测试加载器.loadTestsFromTestCase(测试类)
        self.测试套件.addTest(测试)
    
    def 运行所有测试(self):
        """运行所有测试"""
        测试结果收集器 = unittest.TestResult()
        self.测试套件.run(测试结果收集器)
        
        self.测试结果 = {
            "测试总数": 测试结果收集器.testsRun,
            "成功数": 测试结果收集器.testsRun - len(测试结果收集器.failures) - len(测试结果收集器.errors),
            "失败数": len(测试结果收集器.failures),
            "错误数": len(测试结果收集器.errors),
            "跳过数": len(测试结果收集器.skipped),
            "成功率": (测试结果收集器.testsRun - len(测试结果收集器.failures) - len(测试结果收集器.errors)) / 测试结果收集器.testsRun if 测试结果收集器.testsRun > 0 else 0
        }
        
        # 收集错误信息
        self.错误信息 = {
            "失败": [(test.__str__(), err) for test, err in 测试结果收集器.failures],
            "错误": [(test.__str__(), err) for test, err in 测试结果收集器.errors]
        }
        
        return self.测试结果
    
    def 打印测试结果(self):
        """打印测试结果"""
        print("\n测试结果摘要:")
        print(f"测试总数: {self.测试结果['测试总数']}")
        print(f"成功数: {self.测试结果['成功数']}")
        print(f"失败数: {self.测试结果['失败数']}")
        print(f"错误数: {self.测试结果['错误数']}")
        print(f"跳过数: {self.测试结果['跳过数']}")
        print(f"成功率: {self.测试结果['成功率']*100:.2f}%")
        
        # 打印错误和失败信息
        if self.错误信息["失败"]:
            print("\n失败详情:")
            for 测试, 错误 in self.错误信息["失败"]:
                print(f"\n测试: {测试}")
                print(f"错误: {错误}")
        
        if self.错误信息["错误"]:
            print("\n错误详情:")
            for 测试, 错误 in self.错误信息["错误"]:
                print(f"\n测试: {测试}")
                print(f"错误: {错误}")


class 资金管理测试(unittest.TestCase):
    """资金管理模块测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.资金管理 = 资金管理器(初始资产=1000000, 股票池比例=0.5, 买回保障金比例=0.7)
    
    def test_初始化(self):
        """测试初始化是否正确"""
        self.assertEqual(self.资金管理.初始资产, 1000000)
        self.assertEqual(self.资金管理.当前总资产, 1000000)
        self.assertEqual(self.资金管理.股票池资产, 500000)
        self.assertEqual(self.资金管理.现金池资产, 500000)
        self.assertEqual(self.资金管理.买回保障金, 350000)
        self.assertAlmostEqual(self.资金管理.新建仓资金, 150000, places=2)
    
    def test_更新资产状态(self):
        """测试更新资产状态"""
        self.资金管理.更新资产状态(总资产=1100000, 持仓市值=600000)
        self.assertEqual(self.资金管理.当前总资产, 1100000)
        self.assertEqual(self.资金管理.股票池资产, 600000)
        self.assertEqual(self.资金管理.现金池资产, 500000)
        self.assertEqual(self.资金管理.买回保障金, 350000)
        self.assertAlmostEqual(self.资金管理.新建仓资金, 150000, places=2)
    
    def test_更新持仓(self):
        """测试更新持仓"""
        # 测试买入
        交易记录 = self.资金管理.更新持仓("000001", 1000, 10, True)
        self.assertEqual(self.资金管理.持仓["000001"], 1000)
        self.assertEqual(self.资金管理.持仓成本["000001"], 10)
        self.assertEqual(self.资金管理.现金池资产, 490000)
        
        # 测试卖出
        交易记录 = self.资金管理.更新持仓("000001", 500, 11, False)
        self.assertEqual(self.资金管理.持仓["000001"], 500)
        self.assertEqual(self.资金管理.持仓成本["000001"], 10)
        self.assertEqual(self.资金管理.现金池资产, 495500)
        
        # 检查交易记录
        self.assertEqual(len(self.资金管理.今日交易记录), 2)
    
    def test_检查资金池平衡(self):
        """测试资金池平衡检查"""
        # 初始状态下应该是平衡的
        self.assertFalse(self.资金管理.检查资金池平衡())
        
        # 更新资产状态，使其不平衡
        self.资金管理.更新资产状态(总资产=1100000, 持仓市值=700000)
        self.assertTrue(self.资金管理.检查资金池平衡())
    
    def test_计算建仓数量(self):
        """测试计算建仓数量"""
        数量 = self.资金管理.计算建仓数量("000001", 10, 0.1)
        # 最大可投入 = min(150000, 1000000*0.1) = 100000
        # 数量 = 100000 / 10 / 100 * 100 = 10000
        self.assertEqual(数量, 10000)


class 大象识别测试(unittest.TestCase):
    """大象识别模块测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.识别器 = 大象识别器(大象委托量阈值=1000000, 大象价差阈值=0.05, 确认次数=3, 大象稳定时间=5)
    
    def test_初始化(self):
        """测试初始化是否正确"""
        self.assertEqual(self.识别器.大象委托量阈值, 1000000)
        self.assertEqual(self.识别器.大象价差阈值, 0.05)
        self.assertEqual(self.识别器.确认次数, 3)
        self.assertEqual(self.识别器.大象稳定时间, 5)
        self.assertEqual(self.识别器.大象记录, {})
        self.assertEqual(self.识别器.确认计数, {})
        self.assertEqual(self.识别器.上次盘口, {})
    
    def test_检测大象(self):
        """测试检测大象"""
        # 创建模拟盘口数据
        盘口数据 = {
            "bids": [
                [10.0, 100],  # 买一
                [9.95, 1000000]  # 买二 - 大象
            ],
            "asks": [
                [10.05, 100]  # 卖一
            ]
        }
        
        # 第一次检测，还没有达到确认次数
        结果 = self.识别器.检测大象("000001", 盘口数据)
        self.assertIsNone(结果)
        self.assertEqual(self.识别器.确认计数["000001"], 1)
        
        # 第二次检测，还没有达到确认次数
        结果 = self.识别器.检测大象("000001", 盘口数据)
        self.assertIsNone(结果)
        self.assertEqual(self.识别器.确认计数["000001"], 2)
        
        # 第三次检测，达到确认次数
        结果 = self.识别器.检测大象("000001", 盘口数据)
        self.assertIsNotNone(结果)
        self.assertEqual(self.识别器.确认计数["000001"], 3)
        self.assertEqual(结果["股票代码"], "000001")
        self.assertEqual(结果["价格"], 9.95)
        self.assertEqual(结果["数量"], 1000000)
    
    def test_检查大象稳定性(self):
        """测试大象稳定性检查"""
        # 创建模拟盘口数据
        盘口数据 = {
            "bids": [
                [10.0, 100],
                [9.95, 1000000]
            ],
            "asks": [
                [10.05, 100]
            ]
        }
        
        # 先检测大象三次，确保大象记录被创建
        for _ in range(3):
            self.识别器.检测大象("000001", 盘口数据)
        
        # 确保大象记录已创建
        self.assertIn("000001", self.识别器.大象记录)
        
        # 检查稳定性，由于时间未到，应该返回False
        self.assertFalse(self.识别器.检查大象稳定性("000001"))
        
        # 修改大象检测时间为6秒前
        当前时间 = datetime.now()
        self.识别器.大象记录["000001"]["检测时间"] = 当前时间 - timedelta(seconds=6)
        
        # 再次检查稳定性，应该返回True
        self.assertTrue(self.识别器.检查大象稳定性("000001", 当前时间))
    
    def test_检查大象是否消失(self):
        """测试检查大象是否消失"""
        # 创建初始盘口数据
        初始盘口数据 = {
            "bids": [
                [10.0, 100],
                [9.95, 1000000]
            ],
            "asks": [
                [10.05, 100]
            ]
        }
        
        # 先检测大象三次，确保大象记录被创建
        for _ in range(3):
            self.识别器.检测大象("000001", 初始盘口数据)
        
        # 确保大象记录已创建
        self.assertIn("000001", self.识别器.大象记录)
        
        # 修复检查大象是否消失的测试 - 使用相同的盘口数据检查大象是否消失，应该返回False
        self.assertFalse(self.识别器.检查大象是否消失("000001", 初始盘口数据))
        
        # 创建新的盘口数据，大象数量减少
        新盘口数据 = {
            "bids": [
                [10.0, 100],
                [9.95, 400000]  # 数量减少超过50%
            ],
            "asks": [
                [10.05, 100]
            ]
        }
        
        # 检查大象是否消失，应该返回True
        self.assertTrue(self.识别器.检查大象是否消失("000001", 新盘口数据))


class 交易执行测试(unittest.TestCase):
    """交易执行模块测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.交易执行 = 交易执行器(
            价格偏移量=0.01,
            卖出偏移量倍数=2.0,
            买入偏移量倍数=1.0,
            等待时间=30,
            冷却时间=300,
            止损价格比例=0.5
        )
        
        # 创建模拟大象信息
        self.大象信息 = {
            "股票代码": "000001",
            "档位": 1,
            "价格": 9.95,
            "数量": 1000000,
            "金额": 9950000,
            "买一价": 10.0,
            "卖一价": 10.05,
            "价差": 0.1,
            "价差百分比": 1.0,
            "检测时间": datetime.now()
        }
    
    def test_初始化(self):
        """测试初始化是否正确"""
        self.assertEqual(self.交易执行.价格偏移量, 0.01)
        self.assertEqual(self.交易执行.卖出偏移量倍数, 2.0)
        self.assertEqual(self.交易执行.买入偏移量倍数, 1.0)
        self.assertEqual(self.交易执行.等待时间, 30)
        self.assertEqual(self.交易执行.冷却时间, 300)
        self.assertEqual(self.交易执行.止损价格比例, 0.5)
        self.assertEqual(self.交易执行.活跃订单, {})
        self.assertEqual(self.交易执行.完成订单, [])
        self.assertEqual(self.交易执行.冷却期, {})
        self.assertEqual(self.交易执行.交易对, {})
    
    def test_计算价格(self):
        """测试价格计算"""
        # 测试卖出价格计算
        卖出价格 = self.交易执行.计算卖出价格(self.大象信息)
        self.assertEqual(卖出价格, 9.95 + (0.01 * 2.0))
        
        # 测试买入价格计算
        买入价格 = self.交易执行.计算买入价格(self.大象信息)
        self.assertEqual(买入价格, 9.95 + (0.01 * 1.0))
        
        # 测试止损价格计算
        止损价格 = self.交易执行.计算止损价格(self.大象信息)
        self.assertEqual(止损价格, 9.95 - (0.1 * 0.5))
    
    def test_设置交易冷却期(self):
        """测试设置交易冷却期"""
        self.交易执行.设置交易冷却期("000001")
        self.assertIn("000001", self.交易执行.冷却期)
        
        # 检查冷却期是否在未来
        当前时间 = datetime.now()
        冷却结束时间 = self.交易执行.冷却期["000001"]
        self.assertTrue(冷却结束时间 > 当前时间)
    
    def test_检查交易冷却期(self):
        """测试检查交易冷却期"""
        # 初始状态下应该没有冷却期
        self.assertTrue(self.交易执行.检查交易冷却期("000001"))
        
        # 设置冷却期
        self.交易执行.冷却期["000001"] = datetime.now() + timedelta(seconds=300)
        self.assertFalse(self.交易执行.检查交易冷却期("000001"))
        
        # 设置过期的冷却期
        self.交易执行.冷却期["000001"] = datetime.now() - timedelta(seconds=10)
        self.assertTrue(self.交易执行.检查交易冷却期("000001"))


class 风险控制测试(unittest.TestCase):
    """风险控制模块测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.风险控制 = 风险控制器(
            单笔最大亏损比例=0.001,
            单股最大亏损比例=0.005,
            日内最大亏损比例=0.01,
            单股最大交易次数=10,
            总交易次数限制=100,
            日内风控重置时间="15:00"
        )
        
        # 设置初始总资产
        self.风险控制.更新总资产(1000000)
    
    def test_初始化(self):
        """测试初始化是否正确"""
        self.assertEqual(self.风险控制.单笔最大亏损比例, 0.001)
        self.assertEqual(self.风险控制.单股最大亏损比例, 0.005)
        self.assertEqual(self.风险控制.日内最大亏损比例, 0.01)
        self.assertEqual(self.风险控制.单股最大交易次数, 10)
        self.assertEqual(self.风险控制.总交易次数限制, 100)
        self.assertEqual(self.风险控制.日内风控重置时间, "15:00")
        self.assertEqual(self.风险控制.当前总资产, 1000000)
        self.assertEqual(self.风险控制.日内总盈亏, 0)
        self.assertEqual(self.风险控制.日内总交易次数, 0)
        self.assertEqual(self.风险控制.单股交易次数, {})
        self.assertEqual(self.风险控制.单股盈亏, {})
    
    def test_记录交易盈亏(self):
        """测试记录交易盈亏"""
        # 记录第一笔交易
        self.风险控制.记录交易盈亏("000001", 1000)
        self.assertEqual(self.风险控制.日内总盈亏, 1000)
        self.assertEqual(self.风险控制.单股盈亏["000001"], 1000)
        self.assertEqual(self.风险控制.日内总交易次数, 1)
        self.assertEqual(self.风险控制.单股交易次数["000001"], 1)
        
        # 记录第二笔交易
        self.风险控制.记录交易盈亏("000001", -500)
        self.assertEqual(self.风险控制.日内总盈亏, 500)
        self.assertEqual(self.风险控制.单股盈亏["000001"], 500)
        self.assertEqual(self.风险控制.日内总交易次数, 2)
        self.assertEqual(self.风险控制.单股交易次数["000001"], 2)
    
    def test_检查单笔亏损风险(self):
        """测试检查单笔亏损风险"""
        # 亏损在限制范围内
        self.assertTrue(self.风险控制.检查单笔亏损风险(-1000))  # 1000元亏损，占比0.001，等于限制
        
        # 亏损超出限制
        self.assertFalse(self.风险控制.检查单笔亏损风险(-1100))  # 1100元亏损，占比0.0011，超出限制
    
    def test_检查单股亏损风险(self):
        """测试检查单股亏损风险"""
        # 记录已有亏损
        self.风险控制.记录交易盈亏("000001", -4000)  # 已有4000元亏损，占比0.004
        
        # 亏损在限制范围内
        self.assertTrue(self.风险控制.检查单股亏损风险("000001", -1000))  # 总亏损5000元，占比0.005，等于限制
        
        # 亏损超出限制
        self.assertFalse(self.风险控制.检查单股亏损风险("000001", -1100))  # 总亏损5100元，占比0.0051，超出限制
    
    def test_检查日内亏损风险(self):
        """测试检查日内亏损风险"""
        # 记录已有亏损
        self.风险控制.记录交易盈亏("000001", -5000)  # 已有5000元亏损，占比0.005
        self.风险控制.记录交易盈亏("000002", -4000)  # 总亏损9000元，占比0.009
        
        # 亏损在限制范围内
        self.assertTrue(self.风险控制.检查日内亏损风险(-1000))  # 总亏损10000元，占比0.01，等于限制
        
        # 亏损超出限制
        self.assertFalse(self.风险控制.检查日内亏损风险(-1100))  # 总亏损10100元，占比0.0101，超出限制
    
    def test_检查交易次数限制(self):
        """测试检查交易次数限制"""
        # 记录交易次数
        for i in range(9):
            self.风险控制.记录交易盈亏("000001", 100)
        
        # 交易次数在限制范围内
        self.assertTrue(self.风险控制.检查交易次数限制("000001"))  # 9次交易，未超出限制10次
        
        # 再记录一次，达到限制
        self.风险控制.记录交易盈亏("000001", 100)
        
        # 交易次数达到限制
        self.assertFalse(self.风险控制.检查交易次数限制("000001"))  # 10次交易，达到限制


class 网页管理测试(unittest.TestCase):
    """网页管理模块测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.网页管理 = 网页管理器(端口=8088, 自动打开浏览器=False)
    
    def test_初始化(self):
        """测试初始化是否正确"""
        self.assertEqual(self.网页管理.端口, 8088)
        self.assertEqual(self.网页管理.主机, "localhost")
        self.assertFalse(self.网页管理.自动打开浏览器)
        self.assertIsNone(self.网页管理.服务器)
        self.assertIsNone(self.网页管理.服务器线程)
        self.assertFalse(self.网页管理.运行中)
        self.assertIsNone(self.网页管理.策略)
    
    def test_记录日志(self):
        """测试记录日志功能"""
        self.网页管理.记录日志("测试日志")
        self.assertEqual(len(self.网页管理.日志), 1)
        self.assertEqual(self.网页管理.日志[0]["消息"], "测试日志")
        
        # 测试日志数量限制
        for i in range(self.网页管理.最大日志数量):
            self.网页管理.记录日志(f"日志 {i}")
        
        # 确保日志数量不超过限制
        self.assertEqual(len(self.网页管理.日志), self.网页管理.最大日志数量)


def 运行所有测试():
    """运行所有测试"""
    测试管理 = 测试管理器()
    
    # 添加所有测试类
    测试管理.添加测试类(资金管理测试)
    测试管理.添加测试类(大象识别测试)
    测试管理.添加测试类(交易执行测试)
    测试管理.添加测试类(风险控制测试)
    测试管理.添加测试类(网页管理测试)
    
    # 运行测试
    测试管理.运行所有测试()
    
    # 打印结果
    测试管理.打印测试结果()
    
    return 测试管理.测试结果


if __name__ == "__main__":
    运行所有测试() 