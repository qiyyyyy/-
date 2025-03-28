#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接运行资金管理和大象识别测试
"""
import sys
import os
import unittest
from datetime import datetime, timedelta

# 添加当前目录到系统路径
sys.path.append(os.path.dirname(__file__))


class Mock资金管理器:
    """模拟资金管理器类，用于测试"""
    
    def __init__(self, 初始资产=1000000, 股票池比例=0.5, 买回保障金比例=0.7):
        self.初始资产 = 初始资产
        self.当前总资产 = 初始资产
        self.股票池资产 = 初始资产 * 股票池比例
        self.现金池资产 = 初始资产 * (1 - 股票池比例)
        self.买回保障金 = self.现金池资产 * 买回保障金比例
        self.新建仓资金 = self.现金池资产 - self.买回保障金
        self.持仓 = {}
        self.持仓成本 = {}
        self.今日交易记录 = []
    
    def 更新资产状态(self, 总资产, 持仓市值):
        self.当前总资产 = 总资产
        self.股票池资产 = 持仓市值
        self.现金池资产 = 总资产 - 持仓市值
        self.买回保障金 = self.现金池资产 * 0.7
        self.新建仓资金 = self.现金池资产 - self.买回保障金
    
    def 更新持仓(self, 股票代码, 数量, 价格, 是买入):
        if 股票代码 not in self.持仓:
            self.持仓[股票代码] = 0
            self.持仓成本[股票代码] = 0
        
        交易金额 = 数量 * 价格
        
        if 是买入:
            self.持仓[股票代码] += 数量
            self.持仓成本[股票代码] = 价格
            self.现金池资产 -= 交易金额
        else:
            self.持仓[股票代码] -= 数量
            self.现金池资产 += 交易金额
        
        交易记录 = {
            "时间": datetime.now(),
            "股票代码": 股票代码,
            "数量": 数量,
            "价格": 价格,
            "方向": "买入" if 是买入 else "卖出",
            "金额": 交易金额
        }
        
        self.今日交易记录.append(交易记录)
        return 交易记录
    
    def 检查资金池平衡(self):
        # 计算当前的资金池比例
        股票池比例 = self.股票池资产 / self.当前总资产
        return abs(股票池比例 - 0.5) > 0.1
    
    def 计算建仓数量(self, 股票代码, 价格, 单股最大仓位比例):
        最大可投入 = min(self.新建仓资金, self.当前总资产 * 单股最大仓位比例)
        数量 = int(最大可投入 / 价格 / 100) * 100
        return 数量


class Mock大象识别器:
    """模拟大象识别器类，用于测试"""
    
    def __init__(self, 大象委托量阈值=1000000, 大象价差阈值=0.05, 确认次数=3, 大象稳定时间=5):
        self.大象委托量阈值 = 大象委托量阈值
        self.大象价差阈值 = 大象价差阈值
        self.确认次数 = 确认次数
        self.大象稳定时间 = 大象稳定时间
        self.大象记录 = {}
        self.确认计数 = {}
        self.上次盘口 = {}
    
    def 检测大象(self, 股票代码, 盘口数据, 当前时间=None):
        if 当前时间 is None:
            当前时间 = datetime.now()
        
        self.上次盘口[股票代码] = 盘口数据
        
        # 获取卖一价
        卖一价 = 盘口数据["asks"][0][0] if len(盘口数据["asks"]) > 0 else 0
        if 卖一价 <= 0:
            return None
        
        # 检查大象
        大象信息 = None
        for i in range(1, len(盘口数据["bids"])):
            买价 = 盘口数据["bids"][i][0]
            买量 = 盘口数据["bids"][i][1]
            委托金额 = 买价 * 买量
            
            if 委托金额 >= self.大象委托量阈值:
                大象信息 = {
                    "股票代码": 股票代码,
                    "档位": i,
                    "价格": 买价,
                    "数量": 买量,
                    "金额": 委托金额,
                    "买一价": 盘口数据["bids"][0][0],
                    "卖一价": 卖一价,
                    "价差": 卖一价 - 买价,
                    "价差百分比": (卖一价 - 买价) / 买价 * 100,
                    "检测时间": 当前时间
                }
                break
        
        # 更新确认计数
        if 大象信息:
            if 股票代码 not in self.确认计数:
                self.确认计数[股票代码] = 0
            self.确认计数[股票代码] += 1
            self.大象记录[股票代码] = 大象信息
            
            if self.确认计数[股票代码] >= self.确认次数:
                return 大象信息
        
        return None
    
    def 检查大象稳定性(self, 股票代码, 当前时间=None):
        if 当前时间 is None:
            当前时间 = datetime.now()
        
        if 股票代码 not in self.大象记录:
            return False
        
        大象 = self.大象记录[股票代码]
        时间差 = (当前时间 - 大象["检测时间"]).total_seconds()
        
        return 时间差 >= self.大象稳定时间
    
    def 检查大象是否消失(self, 股票代码, 盘口数据):
        if 股票代码 not in self.大象记录:
            return True
        
        大象 = self.大象记录[股票代码]
        档位 = 大象["档位"]
        
        # 检查盘口数据有效性
        if not isinstance(盘口数据, dict) or "bids" not in 盘口数据:
            return False
        
        # 检查档位是否存在
        if len(盘口数据["bids"]) <= 档位:
            return True
        
        # 检查价格是否变化
        新价格 = 盘口数据["bids"][档位][0]
        if abs(新价格 - 大象["价格"]) > 0.001:
            return True
        
        # 检查数量是否大幅减少
        新数量 = 盘口数据["bids"][档位][1]
        if 新数量 < 大象["数量"] * 0.5:
            return True
        
        return False


class 资金管理测试(unittest.TestCase):
    """资金管理模块测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.资金管理 = Mock资金管理器(初始资产=1000000, 股票池比例=0.5, 买回保障金比例=0.7)
    
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
        self.识别器 = Mock大象识别器(大象委托量阈值=1000000, 大象价差阈值=0.05, 确认次数=3, 大象稳定时间=5)
    
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
        
        # 使用相同的盘口数据检查大象是否消失，应该返回False
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


def 运行所有测试():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(资金管理测试))
    suite.addTests(loader.loadTestsFromTestCase(大象识别测试))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 计算结果
    tests_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    success = tests_run - failures - errors
    
    测试结果 = {
        "测试总数": tests_run,
        "成功数": success,
        "失败数": failures,
        "错误数": errors,
        "跳过数": skipped,
        "成功率": success / tests_run if tests_run > 0 else 0
    }
    
    return 测试结果


if __name__ == "__main__":
    print("开始运行资金管理和大象识别测试...")
    测试结果 = 运行所有测试()
    print("\n测试执行完成。")
    print(f"通过率: {测试结果['成功率']*100:.2f}%")
    print(f"总测试数: {测试结果['测试总数']}")
    print(f"成功: {测试结果['成功数']}")
    print(f"失败: {测试结果['失败数']}")
    print(f"错误: {测试结果['错误数']}") 