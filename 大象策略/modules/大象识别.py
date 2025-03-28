#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大象识别模块 - 识别盘口中的大额买单支撑
"""
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


class 大象识别器:
    """大象识别器类，用于识别盘口中的大单买盘"""
    
    def __init__(
        self, 
        大象委托量阈值: float = 1000000.0, 
        大象价差阈值: float = 0.05, 
        确认次数: int = 3,
        大象稳定时间: int = 5
    ):
        """
        初始化大象识别器
        
        参数:
            大象委托量阈值: 判定为大象的最小委托量(元)
            大象价差阈值: 大象与卖一价的最大价差(%)
            确认次数: 确认大象存在的检测次数
            大象稳定时间: 大象稳定存在的最小秒数
        """
        self.大象委托量阈值 = 大象委托量阈值
        self.大象价差阈值 = 大象价差阈值
        self.确认次数 = 确认次数
        self.大象稳定时间 = 大象稳定时间
        
        # 大象跟踪记录 {股票代码: {大象信息}}
        self.大象记录 = {}
        
        # 确认计数器 {股票代码: 计数}
        self.确认计数 = {}
        
        # 最后一次的盘口数据 {股票代码: 盘口数据}
        self.上次盘口 = {}
    
    def 检测大象(self, 股票代码: str, 盘口数据: Dict, 当前时间: datetime = None) -> Optional[Dict]:
        """
        检测盘口数据中是否存在大象
        
        参数:
            股票代码: 股票代码
            盘口数据: 盘口数据，格式为 {"bids": [[price, volume], ...], "asks": [[price, volume], ...]}
            当前时间: 当前时间，默认为None，将使用系统时间
        
        返回:
            大象信息: 如果存在大象，返回大象信息；否则返回None
        """
        if 当前时间 is None:
            当前时间 = datetime.now()
        
        # 保存本次盘口数据
        self.上次盘口[股票代码] = 盘口数据
        
        # 如果盘口数据为空或无效，返回None
        if not self._检查盘口数据有效性(盘口数据):
            return None
        
        # 获取卖一价
        卖一价 = 盘口数据["asks"][0][0] if len(盘口数据["asks"]) > 0 else 0
        if 卖一价 <= 0:
            return None
        
        # 计算大象价差阈值（绝对值）
        最大价差 = 卖一价 * self.大象价差阈值 / 100
        
        # 从买二开始检查大象（跳过买一）
        大象信息 = None
        for i in range(1, len(盘口数据["bids"])):
            买价 = 盘口数据["bids"][i][0]
            买量 = 盘口数据["bids"][i][1]
            委托金额 = 买价 * 买量
            
            # 检查价差是否在阈值内
            if (卖一价 - 买价) > 最大价差:
                break
            
            # 检查委托量是否超过阈值
            if 委托金额 >= self.大象委托量阈值:
                大象信息 = {
                    "股票代码": 股票代码,
                    "档位": i,
                    "价格": 买价,
                    "数量": 买量,
                    "金额": 委托金额,
                    "买一价": 盘口数据["bids"][0][0] if len(盘口数据["bids"]) > 0 else 0,
                    "卖一价": 卖一价,
                    "价差": 卖一价 - 买价,
                    "价差百分比": (卖一价 - 买价) / 买价 * 100,
                    "检测时间": 当前时间
                }
                break
        
        # 更新确认计数
        if 大象信息:
            # 检查是否是同一个大象（价格相同）
            if 股票代码 in self.大象记录:
                上次大象 = self.大象记录[股票代码]
                if abs(上次大象["价格"] - 大象信息["价格"]) < 0.001:
                    # 同一个大象，累加确认计数
                    if 股票代码 not in self.确认计数:
                        self.确认计数[股票代码] = 0
                    self.确认计数[股票代码] += 1
                else:
                    # 不同大象，重置确认计数
                    self.确认计数[股票代码] = 1
            else:
                # 新大象，设置确认计数为1
                self.确认计数[股票代码] = 1
            
            # 更新大象记录
            self.大象记录[股票代码] = 大象信息
            
            # 如果确认次数达到阈值，返回大象信息
            if self.确认计数[股票代码] >= self.确认次数:
                return 大象信息
        else:
            # 没有检测到大象，重置确认计数
            if 股票代码 in self.确认计数:
                self.确认计数[股票代码] = 0
            
            # 清除大象记录
            if 股票代码 in self.大象记录:
                del self.大象记录[股票代码]
        
        return None
    
    def 检查大象稳定性(self, 股票代码: str, 当前时间: datetime = None) -> bool:
        """
        检查指定股票的大象是否稳定存在
        
        参数:
            股票代码: 股票代码
            当前时间: 当前时间，默认为None，将使用系统时间
        
        返回:
            是否稳定: 如果大象稳定存在，返回True；否则返回False
        """
        if 当前时间 is None:
            当前时间 = datetime.now()
        
        # 检查是否有记录的大象
        if 股票代码 not in self.大象记录:
            return False
        
        # 获取大象记录
        大象 = self.大象记录[股票代码]
        
        # 检查大象是否存在足够长时间
        时间差 = (当前时间 - 大象["检测时间"]).total_seconds()
        return 时间差 >= self.大象稳定时间
    
    def 获取大象信息(self, 股票代码: str) -> Optional[Dict]:
        """
        获取指定股票的大象信息
        
        参数:
            股票代码: 股票代码
        
        返回:
            大象信息: 如果存在大象，返回大象信息；否则返回None
        """
        if 股票代码 in self.大象记录:
            return self.大象记录[股票代码]
        return None
    
    def 检查大象是否消失(self, 股票代码: str, 盘口数据: Dict) -> bool:
        """
        检查指定股票的大象是否已消失
        
        参数:
            股票代码: 股票代码
            盘口数据: 最新盘口数据
        
        返回:
            是否消失: 如果大象已消失，返回True；否则返回False
        """
        # 检查是否有记录的大象
        if 股票代码 not in self.大象记录:
            return True  # 没有记录的大象，视为已消失
        
        # 获取大象记录
        大象 = self.大象记录[股票代码]
        档位 = 大象["档位"]
        
        # 检查盘口数据有效性
        if not self._检查盘口数据有效性(盘口数据):
            return False  # 数据无效时，不能判断大象是否消失，返回False
        
        # 检查对应档位是否还存在
        if len(盘口数据["bids"]) <= 档位:
            return True  # 档位已不存在，大象已消失
        
        # 检查价格是否变化
        新价格 = 盘口数据["bids"][档位][0]
        if abs(新价格 - 大象["价格"]) > 0.001:
            return True  # 价格已变化，大象已消失
        
        # 检查数量是否大幅减少（减少超过50%）
        新数量 = 盘口数据["bids"][档位][1]
        if 新数量 < 大象["数量"] * 0.5:
            return True  # 数量已大幅减少，大象已消失
        
        # 没有满足消失条件，返回False表示大象仍然存在
        return False
    
    def 重置(self, 股票代码: str = None):
        """
        重置大象识别器状态
        
        参数:
            股票代码: 要重置的股票代码，如果为None则重置所有
        """
        if 股票代码:
            if 股票代码 in self.大象记录:
                del self.大象记录[股票代码]
            if 股票代码 in self.确认计数:
                del self.确认计数[股票代码]
            if 股票代码 in self.上次盘口:
                del self.上次盘口[股票代码]
        else:
            self.大象记录 = {}
            self.确认计数 = {}
            self.上次盘口 = {}
    
    def _检查盘口数据有效性(self, 盘口数据: Dict) -> bool:
        """
        检查盘口数据是否有效
        
        参数:
            盘口数据: 盘口数据
        
        返回:
            是否有效: 如果盘口数据有效，返回True；否则返回False
        """
        if not isinstance(盘口数据, dict):
            return False
        
        if "bids" not in 盘口数据 or "asks" not in 盘口数据:
            return False
        
        if not isinstance(盘口数据["bids"], list) or not isinstance(盘口数据["asks"], list):
            return False
        
        if len(盘口数据["bids"]) == 0 or len(盘口数据["asks"]) == 0:
            return False
        
        return True 