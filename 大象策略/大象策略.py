#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大象策略主文件 - 基于vnpy的高频调戏大象策略
适用于中国A股T+1市场，使用调戏大象高频交易获利

作者: AI助手
"""

from typing import Dict, List, Set, Optional, Any
import os
import time
import json
from datetime import datetime, timedelta

from vnpy.trader.constant import (
    Direction,
    Offset,
    Exchange,
    OrderType,
    Status,
    Interval
)
from vnpy.trader.object import (
    TickData,
    BarData,
    OrderData,
    TradeData,
    ContractData,
    PositionData,
    AccountData
)
from vnpy.trader.utility import round_to
from vnpy.trader.event import EVENT_TIMER
# 从新版本导入CTA策略模块
from vnpy_ctastrategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager,
    StopOrder
)

# 导入策略模块 - 修改为相对导入
from modules.资金管理 import 资金管理器
from modules.大象识别 import 大象识别器
from modules.交易执行 import 交易执行器
from modules.风险控制 import 风险控制器
from modules.网页管理 import 网页管理器
from modules.测试模块 import 测试管理器, 运行所有测试
from modules.参数管理 import 参数管理器


class 大象策略(CtaTemplate):
    """
    大象策略主类 - 高频调戏大象交易策略
    
    策略思路：
    1. 识别盘口中的大单买盘或卖盘（大象）
    2. 利用短期价格波动，在大象价格附近高频交易获利
    3. 通过T+1自动建仓机制，适应A股交易规则
    """
    
    # 策略作者
    author = "AI助手"
    
    # 策略参数
    # 大象识别参数
    大象委托量阈值 = 1000000.0  # 判定为大象的最小委托量(元)
    大象价差阈值 = 3  # 大象与卖一价的最大档位数量
    大象确认次数 = 3  # 确认大象存在的检测次数
    大象稳定时间 = 5  # 大象稳定存在的最小秒数
    启用卖单识别 = True  # 是否启用卖单大象识别
    卖单委托量阈值 = 1200000.0  # 判定为卖单大象的最小委托量(元)
    卖单价差阈值 = 3  # 卖单大象与买一价的最大档位数量
    跳过买一价 = False  # 是否跳过买一价搜索大象
    远距大象委托量倍数 = 1.5  # 远距大象委托量阈值倍数
    价差分界点 = 1  # 近距和远距大象的档位分界点
    
    # 交易执行参数
    价格偏移量 = 0.01  # 最小价格变动单位
    卖出偏移量倍数 = 2.0  # 卖出价高于大象价格的偏移量倍数
    买入偏移量倍数 = 1.0  # 买入价高于大象价格的偏移量倍数
    等待时间 = 30  # 等待订单成交的最长时间(秒)
    冷却时间 = 300  # 同一股票交易后的冷却时间(秒)
    止损价格比例 = 0.5  # 相对于大象价差的止损比例
    调戏交易量 = 100  # 调戏模式下每次交易的数量
    最小止盈点数 = 2  # 调戏模式下止盈的点数
    最小止损点数 = 2  # 调戏模式下止损的点数
    
    # 资金管理参数
    单股最大仓位比例 = 0.1  # 单只股票最大持仓占总资产比例
    
    # 风险控制参数
    单笔最大亏损比例 = 0.01  # 单笔交易最大亏损占总资产比例
    单股最大亏损比例 = 0.03  # 单只股票日内最大亏损占总资产比例
    日内最大亏损比例 = 0.05  # 日内最大总亏损占总资产比例
    单股最大交易次数 = 50  # 单只股票日内最大交易次数
    总交易次数限制 = 50  # 日内总交易次数限制
    
    # 网页管理参数
    启用网页管理 = False  # 是否启用网页管理
    网页管理端口 = 8888  # 网页管理端口
    自动打开浏览器 = True  # 是否自动打开浏览器
    
    # 跟踪持仓股票列表
    交易股票列表 = []  # 要交易的股票列表
    
    # 变量
    交易状态 = {}  # 各股票交易状态
    
    def __init__(
        self,
        cta_engine=None,
        strategy_name=None,
        vt_symbol=None,
        setting=None,
        # 策略参数
        股票列表: List[str] = None,
        交易周期: int = 5,
        
        # 资金管理参数
        初始资金: float = 1000000.0,
        单股持仓比例: float = 0.1,
        最大持仓比例: float = 0.8,
        预留资金比例: float = 0.2,
        
        # 大象识别参数
        大象委托量阈值: float = 1000000.0,
        大象价差阈值: float = 0.05,
        确认次数: int = 3,
        大象稳定时间: int = 5,
        启用卖单识别: bool = True,
        卖单委托量阈值: float = 1200000.0,
        卖单价差阈值: float = 0.05,
        跳过买一价: bool = False,
        远距大象委托量倍数: float = 1.5,
        价差分界点: float = 0.02,
        
        # 交易执行参数
        价格偏移量: float = 0.01,
        卖出偏移量倍数: float = 2.0,
        买入偏移量倍数: float = 1.0,
        等待时间: int = 30,
        冷却时间: int = 300,
        止损价格比例: float = 0.5,
        调戏交易量: int = 100,
        最小止盈点数: int = 2,
        最小止损点数: int = 2,
        
        # 风控参数
        单笔最大亏损比例: float = 0.01,
        单股最大亏损比例: float = 0.03,
        日最大亏损比例: float = 0.05,
        最大连续亏损次数: int = 5,
        最大日交易次数: int = 50,
        
        # Web管理参数
        启用Web管理: bool = False,
        Web端口: int = 8888,
        Web用户名: str = "admin",
        Web密码: str = "admin",
        
        # 其他参数
        数据源: str = "ctp",
        回测模式: bool = False,
        日志级别: str = "info",
        
        # 交易日志参数
        启用详细交易日志: bool = True,
        交易日志文件名: str = ""
    ):
        """初始化大象策略"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 初始化参数管理器
        self.参数管理 = 参数管理器(配置目录="config")
        
        # 初始化交易接口属性
        self.交易接口 = None  # 实际运行时会被vnpy设置
        
        # 初始化各个模块
        self.资金管理 = 资金管理器(
            初始资产=0,
            股票池比例=0.5,  # 不再使用股票池比例，但保留兼容性
            买回保障金比例=0.3  # 降低买回保障金比例
        )
        
        # 初始化时使用全局参数初始化各模块
        大象识别参数 = self.参数管理.获取参数("global", "大象识别", "大象委托量阈值", 大象委托量阈值)
        self.大象识别 = 大象识别器(
            大象委托量阈值=self.参数管理.获取参数("global", "大象识别", "大象委托量阈值", 大象委托量阈值),
            大象价差阈值=self.参数管理.获取参数("global", "大象识别", "大象价差阈值", 大象价差阈值),
            确认次数=self.参数管理.获取参数("global", "大象识别", "大象确认次数", 确认次数),
            大象稳定时间=self.参数管理.获取参数("global", "大象识别", "大象稳定时间", 大象稳定时间),
            启用卖单识别=self.参数管理.获取参数("global", "大象识别", "启用卖单识别", 启用卖单识别),
            卖单委托量阈值=self.参数管理.获取参数("global", "大象识别", "卖单委托量阈值", 卖单委托量阈值),
            卖单价差阈值=self.参数管理.获取参数("global", "大象识别", "卖单价差阈值", 卖单价差阈值),
            跳过买一价=self.参数管理.获取参数("global", "大象识别", "跳过买一价", 跳过买一价),
            远距大象委托量倍数=self.参数管理.获取参数("global", "大象识别", "远距大象委托量倍数", 远距大象委托量倍数),
            价差分界点=self.参数管理.获取参数("global", "大象识别", "价差分界点", 价差分界点)
        )
        
        # 先初始化风险控制器
        self.风险控制 = 风险控制器(
            单笔最大亏损比例=self.参数管理.获取参数("global", "风险控制", "单笔最大亏损比例", 单笔最大亏损比例),
            单股最大亏损比例=self.参数管理.获取参数("global", "风险控制", "单股最大亏损比例", 单股最大亏损比例),
            日内最大亏损比例=self.参数管理.获取参数("global", "风险控制", "日内最大亏损比例", 日最大亏损比例),
            单股最大交易次数=self.参数管理.获取参数("global", "风险控制", "单股最大交易次数", 最大日交易次数),
            总交易次数限制=self.参数管理.获取参数("global", "风险控制", "总交易次数限制", 最大日交易次数)
        )
        
        # 再初始化交易执行器
        self.交易执行 = 交易执行器(
            交易接口=self,  # 传入self作为交易接口
            风控=self.风险控制,  # 使用已初始化的风险控制器
            价格偏移量=self.参数管理.获取参数("global", "交易执行", "价格偏移量", 价格偏移量),
            卖出偏移量倍数=self.参数管理.获取参数("global", "交易执行", "卖出偏移量倍数", 卖出偏移量倍数),
            买入偏移量倍数=self.参数管理.获取参数("global", "交易执行", "买入偏移量倍数", 买入偏移量倍数),
            等待时间=self.参数管理.获取参数("global", "交易执行", "等待时间", 等待时间),
            冷却时间=self.参数管理.获取参数("global", "交易执行", "冷却时间", 冷却时间),
            止损价格比例=self.参数管理.获取参数("global", "交易执行", "止损价格比例", 止损价格比例),
            交易量=self.参数管理.获取参数("global", "交易执行", "调戏交易量", 调戏交易量),
            最小止盈点数=self.参数管理.获取参数("global", "交易执行", "最小止盈点数", 最小止盈点数),
            最小止损点数=self.参数管理.获取参数("global", "交易执行", "最小止损点数", 最小止损点数)
        )
        
        # 初始化网页管理器
        self.网页管理 = None
        if 启用Web管理:
            self.网页管理 = 网页管理器(
                端口=Web端口,
                自动打开浏览器=(Web用户名 != ""),  # 如果有用户名则自动打开浏览器
                参数管理器=self.参数管理  # 传入参数管理器
            )
        
        # 初始化测试管理器
        self.测试管理器 = None
        
        # 行情订阅标志
        self.已订阅股票 = set()
        
        # 策略状态
        self.策略状态 = "初始化"
        self.上次检查时间 = None
        
        # 日志和数据保存路径
        self.日志路径 = "logs/"
        self.数据路径 = "data/"
        
        # 确保目录存在
        os.makedirs(self.日志路径, exist_ok=True)
        os.makedirs(self.数据路径, exist_ok=True)
        
        # 保存参数
        self.股票列表 = 股票列表 or []
        self.交易周期 = 交易周期
        
        # 交易日志设置
        self.启用详细交易日志 = 启用详细交易日志
        self.交易日志文件名 = 交易日志文件名 or f"大象策略交易日志_{datetime.now().strftime('%Y%m%d')}.log"
        self.交易日志文件路径 = os.path.join(self.日志路径, self.交易日志文件名)
        
        # 初始化交易日志
        if self.启用详细交易日志:
            self._初始化交易日志文件()
    
    def on_init(self):
        """策略初始化完成"""
        self.write_log("策略初始化完成")
        self.策略状态 = "就绪"
        self.上次检查时间 = datetime.now()
        
        # 加载交易股票列表
        self._加载交易股票()
        
        # 订阅行情
        self._订阅股票行情()
        
        # 启动网页管理器
        if self.网页管理:
            self.网页管理.连接策略(self)
            self.网页管理.启动()
            self.write_log(f"网页管理服务已启动，端口:{self.网页管理.端口}")
    
    def on_start(self):
        """策略启动"""
        self.write_log("策略启动")
        self.策略状态 = "运行中"
        
        # 更新账户信息
        try:
            self._更新账户信息()
        except Exception as e:
            self.write_log(f"更新账户信息失败: {e}")
        
        # 检查未完成订单
        try:
            self._检查未完成订单()
        except Exception as e:
            self.write_log(f"检查未完成订单失败: {e}")
    
    def on_stop(self):
        """策略停止"""
        self.write_log("策略停止")
        self.策略状态 = "已停止"
        
        # 取消所有活跃订单
        self._取消所有活跃订单()
        
        # 关闭网页管理器
        if self.网页管理:
            self.网页管理.关闭()
    
    def on_tick(self, tick: TickData):
        """
        收到行情Tick推送
        """
        # 提取股票代码
        股票代码 = tick.symbol
        
        # 记录最新价格
        self._更新最新价格(股票代码, tick.last_price)
        
        # 处理盘口数据
        盘口数据 = {
            "时间戳": int(tick.datetime.timestamp() * 1000),
            "买盘": [(tick.bid_price_1, tick.bid_volume_1),
                   (tick.bid_price_2, tick.bid_volume_2),
                   (tick.bid_price_3, tick.bid_volume_3),
                   (tick.bid_price_4, tick.bid_volume_4),
                   (tick.bid_price_5, tick.bid_volume_5)],
            "卖盘": [(tick.ask_price_1, tick.ask_volume_1),
                   (tick.ask_price_2, tick.ask_volume_2),
                   (tick.ask_price_3, tick.ask_volume_3),
                   (tick.ask_price_4, tick.ask_volume_4),
                   (tick.ask_price_5, tick.ask_volume_5)],
            "最新价": tick.last_price
        }
        
        self._处理盘口数据(股票代码, 盘口数据, tick.datetime)
    
    def on_bar(self, bar: BarData):
        """
        收到K线数据推送
        """
        # 提取股票代码
        股票代码 = bar.symbol
        
        # 记录收盘价
        self._更新最新价格(股票代码, bar.close_price)
    
    def on_order(self, order: OrderData):
        """
        收到委托变化推送
        """
        # 更新订单状态
        self.交易执行.更新订单状态(order)
    
    def on_trade(self, trade: TradeData):
        """
        收到成交推送
        """
        # 更新成交记录
        self.交易执行.更新成交记录(trade)
        
        # 更新资金管理
        是买入 = trade.direction == Direction.LONG
        self.资金管理.更新持仓(trade.symbol, trade.volume, trade.price, 是买入)
        
        # 日志记录
        方向 = "买入" if 是买入 else "卖出"
        self.write_log(f"成交: {trade.symbol} {方向} {trade.volume}股 价格:{trade.price}")
    
    def on_timer(self, interval: int):
        """
        定时器回调函数
        """
        # 每隔一段时间执行一次
        当前时间 = datetime.now()
        if self.上次检查时间:
            间隔秒数 = (当前时间 - self.上次检查时间).total_seconds()
            
            # 交易时间内每隔交易周期检查一次
            if 间隔秒数 >= self.交易周期 and self.是否交易时间(当前时间):
                # 更新账户信息
                self._更新账户信息()
                
                # 检查订单超时
                self.交易执行.检查订单超时(当前时间)
                
                # 更新上次检查时间
                self.上次检查时间 = 当前时间
    
    def _加载交易股票(self):
        """加载要交易的股票列表"""
        try:
            # 使用参数管理器加载股票列表
            股票列表 = self.参数管理.获取股票列表()
            if 股票列表:
                self.交易股票列表 = 股票列表
                self.write_log(f"从配置文件加载交易股票列表，共{len(self.交易股票列表)}只")
            else:
                # 如果配置文件不存在，使用当前持仓作为交易股票
                self.write_log("配置文件不存在或为空，将使用当前持仓作为交易股票")
                self._更新交易股票列表()
        except Exception as e:
            self.write_log(f"加载交易股票列表出错: {e}")
            self._更新交易股票列表()
    
    def _更新交易股票列表(self):
        """根据当前持仓更新交易股票列表"""
        if not self.cta_engine:
            self.write_log("CTA引擎未初始化，无法更新交易股票列表")
            self.交易股票列表 = []  # 设置为空列表，避免错误
            return
            
        if not hasattr(self.cta_engine, "main_engine") or not self.cta_engine.main_engine:
            self.write_log("CTA引擎的main_engine未初始化，无法更新交易股票列表")
            self.交易股票列表 = []  # 设置为空列表，避免错误
            return
            
        try:
            positions = self.cta_engine.main_engine.get_all_positions()
            持仓股票 = [position.symbol for position in positions if position.volume > 0]
            
            self.交易股票列表 = 持仓股票
            self.write_log(f"更新交易股票列表，共{len(self.交易股票列表)}只")
            
            # 保存到配置文件
            if hasattr(self, "参数管理") and self.参数管理:
                self.参数管理.设置股票列表(self.交易股票列表)
        except Exception as e:
            self.write_log(f"更新交易股票列表出错: {e}")
            # 设置为空列表，避免错误
            self.交易股票列表 = []
    
    def _订阅股票行情(self):
        """订阅交易股票的行情"""
        if not self.cta_engine:
            self.write_log("CTA引擎未初始化，无法订阅行情")
            return
        
        # 如果股票列表为空，尝试从配置文件加载
        if not self.交易股票列表 and hasattr(self, "参数管理") and self.参数管理:
            try:
                股票列表 = self.参数管理.获取股票列表()
                if 股票列表:
                    self.交易股票列表 = 股票列表
                    self.write_log(f"从配置文件加载交易股票列表，共{len(self.交易股票列表)}只")
            except Exception as e:
                self.write_log(f"加载交易股票列表出错: {e}")
            
        for 股票代码 in self.交易股票列表:
            if 股票代码 not in self.已订阅股票:
                try:
                    交易所 = self._判断交易所(股票代码)
                    vt_symbol = f"{股票代码}.{交易所.value}"
                    
                    self.cta_engine.subscribe(vt_symbol)
                    self.已订阅股票.add(股票代码)
                    self.write_log(f"订阅行情: {vt_symbol}")
                except Exception as e:
                    self.write_log(f"订阅行情失败 {股票代码}: {e}")
    
    def _判断交易所(self, 股票代码: str) -> Exchange:
        """
        根据股票代码判断交易所
        
        参数:
            股票代码: 股票代码
            
        返回:
            交易所: Exchange.SSE或Exchange.SZSE
        """
        if 股票代码.startswith("6") or 股票代码.startswith("5"):
            return Exchange.SSE  # 上海交易所
        else:
            return Exchange.SZSE  # 深圳交易所
    
    def _更新账户信息(self):
        """更新账户资产信息"""
        if not self.cta_engine:
            self.write_log("CTA引擎未初始化，无法更新账户信息")
            return
            
        if not hasattr(self.cta_engine, "main_engine") or not self.cta_engine.main_engine:
            self.write_log("CTA引擎的main_engine未初始化，无法更新账户信息")
            return
            
        try:
            # 获取账户信息
            account = self.cta_engine.main_engine.get_account()
            
            # 获取持仓信息
            positions = self.cta_engine.main_engine.get_all_positions()
            持仓市值 = sum(position.price * position.volume for position in positions)
            
            # 更新资金管理模块
            总资产 = account.balance
            self.资金管理.更新资产状态(总资产, 持仓市值)
            
            # 更新风险控制模块
            self.风险控制.更新总资产(总资产)
            
            # 更新持仓信息
            for position in positions:
                if position.volume > 0:
                    self.资金管理.持仓[position.symbol] = position.volume
                    self.资金管理.持仓成本[position.symbol] = position.price
            
            # 日志记录
            self.write_log(f"账户信息更新: 总资产 {总资产:.2f}, 持仓市值 {持仓市值:.2f}")
        except Exception as e:
            self.write_log(f"更新账户信息出错: {e}")
            
    def _检查未完成订单(self):
        """检查未完成订单，必要时取消"""
        if not self.cta_engine or not hasattr(self.cta_engine, "main_engine") or not self.cta_engine.main_engine:
            self.write_log("CTA引擎未初始化，无法检查未完成订单")
            return
            
        try:
            orders = self.cta_engine.main_engine.get_all_active_orders()
            
            if orders:
                self.write_log(f"发现{len(orders)}个未完成订单，尝试取消")
                for order in orders:
                    self.cancel_order(order.vt_orderid)
        except Exception as e:
            self.write_log(f"检查未完成订单出错: {e}")
            
    def _取消所有活跃订单(self):
        """取消所有活跃订单"""
        if not self.cta_engine or not hasattr(self.cta_engine, "main_engine") or not self.cta_engine.main_engine:
            self.write_log("CTA引擎未初始化，无法取消活跃订单")
            return
            
        try:
            orders = self.cta_engine.main_engine.get_all_active_orders()
            
            if orders:
                self.write_log(f"取消{len(orders)}个活跃订单")
                for order in orders:
                    self.cancel_order(order.vt_orderid)
        except Exception as e:
            self.write_log(f"取消活跃订单出错: {e}")
    
    def _处理盘口数据(self, 股票代码: str, 盘口数据: Dict, 当前时间: datetime = None):
        """
        处理股票的盘口数据，检测大象并执行交易
        
        参数:
            股票代码: 股票代码
            盘口数据: 盘口深度数据
            当前时间: 当前时间
        """
        if 当前时间 is None:
            当前时间 = datetime.now()
        
        # 检查当前是否在交易时间
        if not self.是否交易时间(当前时间):
            return
        
        # 获取品种特定参数
        品种参数 = self.参数管理.获取品种所有参数(股票代码)
        
        # 检查风控状态
        if self.风险控制.检查全局风控():
            self.write_log(f"风控触发，暂停交易 {股票代码}")
            return
        
        # 更新大象识别器参数为品种特定参数
        大象识别参数 = {}
        if "大象识别" in 品种参数:
            for 参数名, 参数值 in 品种参数["大象识别"].items():
                大象识别参数[参数名] = 参数值
                # 设置对象属性
                if hasattr(self.大象识别, 参数名):
                    setattr(self.大象识别, 参数名, 参数值)
        
        # 检测大象
        买单大象信息, 卖单大象信息 = self.大象识别.检测大象(股票代码, 盘口数据, 当前时间)
        
        # 处理买单大象信号
        if 买单大象信息:
            self.write_log(f"检测到买单大象: {股票代码} 价格:{买单大象信息['价格']} 金额:{买单大象信息['金额']}")
            买单大象信息["股票代码"] = 股票代码
            买单大象信息["类型"] = "买单大象"
            self._处理大象交易信号(股票代码, 买单大象信息, 盘口数据)
        
        # 处理卖单大象信号（如果启用了卖单识别）
        if 卖单大象信息:
            self.write_log(f"检测到卖单大象: {股票代码} 价格:{卖单大象信息['价格']} 金额:{卖单大象信息['金额']}")
            卖单大象信息["股票代码"] = 股票代码
            卖单大象信息["类型"] = "卖单大象"
            self._处理大象交易信号(股票代码, 卖单大象信息, 盘口数据)
    
    def _处理大象交易信号(self, 股票代码: str, 大象信息: Dict, 盘口数据: Dict):
        """
        处理大象交易信号，根据大象位置执行相应交易策略
        
        参数:
            股票代码: 股票代码
            大象信息: 大象信息
            盘口数据: 盘口深度数据
        """
        # 检查该股票是否在交易中
        if 股票代码 in self.交易状态 and self.交易状态[股票代码].get("状态") != "空闲":
            return
        
        # 获取品种特定参数
        品种参数 = self.参数管理.获取品种所有参数(股票代码)
        
        # 更新交易执行器参数
        if "交易执行" in 品种参数:
            for 参数名, 参数值 in 品种参数["交易执行"].items():
                if hasattr(self.交易执行, 参数名):
                    setattr(self.交易执行, 参数名, 参数值)
        
        # 检查是否在交易冷却期
        if not self.交易执行.检查交易冷却期(股票代码):
            return
        
        # 检查大象稳定性
        if not self.大象识别.检查大象稳定性(股票代码):
            return
        
        # 更新风险控制器参数
        if "风险控制" in 品种参数:
            for 参数名, 参数值 in 品种参数["风险控制"].items():
                if hasattr(self.风险控制, 参数名):
                    setattr(self.风险控制, 参数名, 参数值)
        
        # 检查风险
        允许交易, 拒绝原因 = self.风险控制.检查交易风险(股票代码)
        if not 允许交易:
            self.write_log(f"风险控制拒绝交易 {股票代码}: {拒绝原因}")
            return
        
        # 更新资金管理器参数
        if "资金管理" in 品种参数:
            for 参数名, 参数值 in 品种参数["资金管理"].items():
                if hasattr(self.资金管理, 参数名):
                    setattr(self.资金管理, 参数名, 参数值)
        
        # 记录交易状态
        self.交易状态[股票代码] = {
            "状态": "交易中",
            "大象信息": 大象信息,
            "开始时间": datetime.now()
        }
        
        # 根据大象类型执行不同的交易策略
        大象类型 = 大象信息.get("类型", "")
        
        if "买单大象" in 大象类型:
            # 下方大象策略: 先买入，等价格上涨后卖出
            self.write_log(f"检测到下方大象，执行买入策略: {股票代码}")
            self._执行下方大象策略(股票代码, 大象信息, 盘口数据)
        elif "卖单大象" in 大象类型:
            # 上方大象策略: 先卖出，等价格下跌后买回
            self.write_log(f"检测到上方大象，执行卖出策略: {股票代码}")
            self._执行上方大象策略(股票代码, 大象信息, 盘口数据)
        else:
            self.write_log(f"未识别的大象类型: {大象类型}")
            self._清理交易状态(股票代码)
            return
        
        # 设置冷却期
        self.交易执行.设置交易冷却期(股票代码)
    
    def _执行下方大象策略(self, 股票代码: str, 大象信息: Dict, 盘口数据: Dict):
        """
        执行下方大象策略：以盘口价格买入，等价格上涨后卖出
        
        参数:
            股票代码: 股票代码
            大象信息: 大象信息
            盘口数据: 盘口深度数据
        """
        # 获取当前盘口价格
        if not 盘口数据 or not 盘口数据.get("asks") or not 盘口数据["asks"][0]:
            self.write_log(f"无法获取盘口数据: {股票代码}")
            self._清理交易状态(股票代码)
            return
            
        卖一价 = 盘口数据["asks"][0][0]
        
        # 计算买入价格和数量
        买入价格 = 卖一价  # 以卖一价买入
        买入数量 = self.交易执行.交易量  # 使用预设的交易量
        
        # 计算预期卖出价格
        预期卖出价格 = 买入价格 * (1 + self.交易执行.最小止盈点数 / 100)  # 按点数计算
        
        # 计算止损价格
        止损价格 = 大象信息["价格"] - self.交易执行.最小止损点数 / 100 * 买入价格
        
        # 发送买入订单
        交易所 = self._判断交易所(股票代码)
        vt_symbol = f"{股票代码}.{交易所.value}"
        
        # 记录交易计划
        self.交易状态[股票代码].update({
            "状态": "买入中",
            "买入价格": 买入价格,
            "买入数量": 买入数量,
            "预期卖出价格": 预期卖出价格,
            "止损价格": 止损价格
        })
        
        # 记录交易日志
        self._记录交易日志({
            "股票代码": 股票代码,
            "类型": "下方大象策略",
            "操作": "买入",
            "价格": 买入价格,
            "数量": 买入数量,
            "状态": "发送订单",
            "大象类型": "买单大象",
            "大象价格": 大象信息.get("价格", 0),
            "大象金额": 大象信息.get("金额", 0)
        })
        
        # 执行买入
        order_id = self.buy(vt_symbol, 买入价格, 买入数量)
        
        if order_id:
            self.交易状态[股票代码]["买入订单ID"] = order_id
            self.write_log(f"下方大象策略发送买入订单: {股票代码} {买入数量}股 @ {买入价格}")
        else:
            self.write_log(f"下方大象策略买入订单发送失败: {股票代码}")
            self._清理交易状态(股票代码)
            
            # 记录交易日志
            self._记录交易日志({
                "股票代码": 股票代码,
                "类型": "下方大象策略",
                "操作": "买入",
                "价格": 买入价格,
                "数量": 买入数量,
                "状态": "发送失败",
                "大象类型": "买单大象",
                "大象价格": 大象信息.get("价格", 0),
                "大象金额": 大象信息.get("金额", 0)
            })
    
    def _执行上方大象策略(self, 股票代码: str, 大象信息: Dict, 盘口数据: Dict):
        """
        执行上方大象策略：先卖出，等价格下跌后买回
        
        参数:
            股票代码: 股票代码
            大象信息: 大象信息
            盘口数据: 盘口深度数据
        """
        # 获取当前盘口价格
        if not 盘口数据 or not 盘口数据.get("bids") or not 盘口数据["bids"][0]:
            self.write_log(f"无法获取盘口数据: {股票代码}")
            self._清理交易状态(股票代码)
            return
            
        买一价 = 盘口数据["bids"][0][0]
        
        # 计算卖出价格和数量
        卖出价格 = 买一价  # 以买一价卖出
        卖出数量 = self.交易执行.交易量  # 使用预设的交易量
        
        # 计算预期买回价格
        预期买回价格 = 卖出价格 * (1 - self.交易执行.最小止盈点数 / 100)  # 按点数计算
        
        # 计算止损价格
        止损价格 = 大象信息["价格"] + self.交易执行.最小止损点数 / 100 * 卖出价格
        
        # 发送卖出订单
        交易所 = self._判断交易所(股票代码)
        vt_symbol = f"{股票代码}.{交易所.value}"
        
        # 记录交易计划
        self.交易状态[股票代码].update({
            "状态": "卖出中",
            "卖出价格": 卖出价格,
            "卖出数量": 卖出数量,
            "预期买回价格": 预期买回价格,
            "止损价格": 止损价格
        })
        
        # 记录交易日志
        self._记录交易日志({
            "股票代码": 股票代码,
            "类型": "上方大象策略",
            "操作": "卖出",
            "价格": 卖出价格,
            "数量": 卖出数量,
            "状态": "发送订单",
            "大象类型": "卖单大象",
            "大象价格": 大象信息.get("价格", 0),
            "大象金额": 大象信息.get("金额", 0)
        })
        
        # 执行卖出
        order_id = self.sell(vt_symbol, 卖出价格, 卖出数量)
        
        if order_id:
            self.交易状态[股票代码]["卖出订单ID"] = order_id
            self.write_log(f"上方大象策略发送卖出订单: {股票代码} {卖出数量}股 @ {卖出价格}")
        else:
            self.write_log(f"上方大象策略卖出订单发送失败: {股票代码}")
            self._清理交易状态(股票代码)
            
            # 记录交易日志
            self._记录交易日志({
                "股票代码": 股票代码,
                "类型": "上方大象策略",
                "操作": "卖出",
                "价格": 卖出价格,
                "数量": 卖出数量,
                "状态": "发送失败",
                "大象类型": "卖单大象",
                "大象价格": 大象信息.get("价格", 0),
                "大象金额": 大象信息.get("金额", 0)
            })
    
    def _处理订单完成(self, order: OrderData):
        """
        处理订单完成事件
        
        参数:
            order: 订单数据
        """
        if order.status not in [Status.ALLTRADED, Status.CANCELLED, Status.REJECTED]:
            return
            
        vt_symbol = order.vt_symbol
        股票代码 = vt_symbol.split('.')[0]
        
        # 检查该股票是否有活跃交易
        if 股票代码 not in self.交易状态:
            return
            
        交易状态 = self.交易状态[股票代码]
        
        # ==== 处理下方大象策略 ====
        # 买入订单成交后，等待价格上涨到目标价格再卖出
        if "买入订单ID" in 交易状态 and 交易状态["买入订单ID"] == order.vt_orderid and 交易状态.get("状态") == "买入中":
            if order.status == Status.ALLTRADED:
                # 买入成交，更新状态
                self.write_log(f"下方大象策略买入成交: {股票代码} {order.volume_traded}股 @ {order.price}")
                交易状态.update({
                    "状态": "持有中",
                    "买入成交价格": order.price,
                    "买入成交数量": order.volume_traded,
                    "买入成交时间": datetime.now()
                })
                
                # 记录交易日志
                self._记录交易日志({
                    "股票代码": 股票代码,
                    "类型": "下方大象策略",
                    "操作": "买入",
                    "价格": order.price,
                    "数量": order.volume_traded,
                    "状态": "成交",
                    "大象类型": 交易状态.get("大象信息", {}).get("类型", ""),
                    "大象价格": 交易状态.get("大象信息", {}).get("价格", 0),
                    "大象金额": 交易状态.get("大象信息", {}).get("金额", 0)
                })
                
                # 设置卖出价格
                卖出价格 = 交易状态.get("预期卖出价格", order.price * (1 + self.交易执行.最小止盈点数 / 100))
                
                # 发送卖出订单
                交易所 = self._判断交易所(股票代码)
                vt_symbol = f"{股票代码}.{交易所.value}"
                卖出数量 = order.volume_traded
                
                # 记录交易日志
                self._记录交易日志({
                    "股票代码": 股票代码,
                    "类型": "下方大象策略",
                    "操作": "卖出",
                    "价格": 卖出价格,
                    "数量": 卖出数量,
                    "状态": "发送订单",
                    "大象类型": 交易状态.get("大象信息", {}).get("类型", ""),
                    "大象价格": 交易状态.get("大象信息", {}).get("价格", 0),
                    "大象金额": 交易状态.get("大象信息", {}).get("金额", 0)
                })
                
                order_id = self.sell(vt_symbol, 卖出价格, 卖出数量)
                
                if order_id:
                    交易状态.update({
                        "状态": "卖出中",
                        "卖出订单ID": order_id,
                        "卖出价格": 卖出价格,
                        "卖出数量": 卖出数量
                    })
                    self.write_log(f"下方大象策略发送卖出订单: {股票代码} {卖出数量}股 @ {卖出价格}")
            else:
                self.write_log(f"下方大象策略卖出订单发送失败: {股票代码}")
                self._清理交易状态(股票代码)
                
                # 记录交易日志
                self._记录交易日志({
                    "股票代码": 股票代码,
                    "类型": "下方大象策略",
                    "操作": "卖出",
                    "价格": 卖出价格,
                    "数量": 卖出数量,
                    "状态": "发送失败",
                    "大象类型": 交易状态.get("大象信息", {}).get("类型", ""),
                    "大象价格": 交易状态.get("大象信息", {}).get("价格", 0),
                    "大象金额": 交易状态.get("大象信息", {}).get("金额", 0)
                })
        elif "卖出订单ID" in 交易状态 and 交易状态["卖出订单ID"] == order.vt_orderid and 交易状态.get("状态") == "卖出中":
            if order.status == Status.ALLTRADED:
                # 卖出成交，计算盈亏
                self.write_log(f"下方大象策略卖出成交: {股票代码} {order.volume_traded}股 @ {order.price}")
                交易状态.update({
                    "状态": "已完成",
                    "卖出成交价格": order.price,
                    "卖出成交数量": order.volume_traded,
                    "卖出成交时间": datetime.now()
                })
                
                # 计算盈亏
                if "买入成交价格" in 交易状态 and "卖出成交价格" in 交易状态:
                    买入价格 = 交易状态["买入成交价格"]
                    卖出价格 = 交易状态["卖出成交价格"]
                    交易数量 = min(交易状态.get("买入成交数量", 0), 交易状态.get("卖出成交数量", 0))
                    
                    盈亏 = (卖出价格 - 买入价格) * 交易数量
                    手续费 = (卖出价格 + 买入价格) * 交易数量 * 0.0003  # 假设手续费为万三
                    净盈亏 = 盈亏 - 手续费
                    
                    交易状态.update({
                        "盈亏": 盈亏,
                        "手续费": 手续费,
                        "净盈亏": 净盈亏
                    })
                    
                    self.write_log(f"下方大象策略交易完成: {股票代码} 盈亏: {盈亏:.2f}, 净盈亏: {净盈亏:.2f}")
                    
                    # 记录盈亏
                    self.风险控制.记录交易盈亏(股票代码, 净盈亏)
                
                # 清理交易状态
                self._清理交易状态(股票代码)
            else:
                # 卖出订单被取消或拒绝
                self.write_log(f"下方大象策略卖出订单未成交: {股票代码} {order.status}")
                self._清理交易状态(股票代码)
        
        # ==== 处理上方大象策略 ====
        # 卖出订单成交后，等待价格下跌到目标价格再买回
        elif "卖出订单ID" in 交易状态 and 交易状态["卖出订单ID"] == order.vt_orderid and 交易状态.get("状态") == "卖出中" and 交易状态.get("大象信息", {}).get("类型") == "卖单大象":
            if order.status == Status.ALLTRADED:
                # 卖出成交，更新状态
                self.write_log(f"上方大象策略卖出成交: {股票代码} {order.volume_traded}股 @ {order.price}")
                交易状态.update({
                    "状态": "已卖出待买回",
                    "卖出成交价格": order.price,
                    "卖出成交数量": order.volume_traded,
                    "卖出成交时间": datetime.now()
                })
                
                # 设置买回价格
                买回价格 = 交易状态.get("预期买回价格", order.price * (1 - self.交易执行.最小止盈点数 / 100))
                
                # 发送买回订单
                交易所 = self._判断交易所(股票代码)
                vt_symbol = f"{股票代码}.{交易所.value}"
                买回数量 = order.volume_traded
                
                order_id = self.buy(vt_symbol, 买回价格, 买回数量)
                
                if order_id:
                    交易状态.update({
                        "状态": "买回中",
                        "买入订单ID": order_id,
                        "买入价格": 买回价格,
                        "买入数量": 买回数量
                    })
                    self.write_log(f"上方大象策略发送买回订单: {股票代码} {买回数量}股 @ {买回价格}")
                else:
                    self.write_log(f"上方大象策略买回订单发送失败: {股票代码}")
                    self._清理交易状态(股票代码)
            else:
                # 卖出订单被取消或拒绝
                self.write_log(f"上方大象策略卖出订单未成交: {股票代码} {order.status}")
                self._清理交易状态(股票代码)
        
        # 买回订单成交后，计算盈亏并完成交易
        elif "买入订单ID" in 交易状态 and 交易状态["买入订单ID"] == order.vt_orderid and 交易状态.get("状态") == "买回中":
            if order.status == Status.ALLTRADED:
                # 买回成交，计算盈亏
                self.write_log(f"上方大象策略买回成交: {股票代码} {order.volume_traded}股 @ {order.price}")
                交易状态.update({
                    "状态": "已完成",
                    "买入成交价格": order.price,
                    "买入成交数量": order.volume_traded,
                    "买入成交时间": datetime.now()
                })
                
                # 计算盈亏
                if "卖出成交价格" in 交易状态 and "买入成交价格" in 交易状态:
                    卖出价格 = 交易状态["卖出成交价格"]
                    买入价格 = 交易状态["买入成交价格"]
                    交易数量 = min(交易状态.get("卖出成交数量", 0), 交易状态.get("买入成交数量", 0))
                    
                    盈亏 = (卖出价格 - 买入价格) * 交易数量
                    手续费 = (卖出价格 + 买入价格) * 交易数量 * 0.0003  # 假设手续费为万三
                    净盈亏 = 盈亏 - 手续费
                    
                    交易状态.update({
                        "盈亏": 盈亏,
                        "手续费": 手续费,
                        "净盈亏": 净盈亏
                    })
                    
                    self.write_log(f"上方大象策略交易完成: {股票代码} 盈亏: {盈亏:.2f}, 净盈亏: {净盈亏:.2f}")
                    
                    # 记录盈亏
                    self.风险控制.记录交易盈亏(股票代码, 净盈亏)
                
                # 清理交易状态
                self._清理交易状态(股票代码)
            else:
                # 买回订单被取消或拒绝
                self.write_log(f"上方大象策略买回订单未成交: {股票代码} {order.status}")
                self._清理交易状态(股票代码)
    
    def _处理订单取消(self, order: OrderData):
        """
        处理订单取消
        
        参数:
            order: 订单数据
        """
        股票代码 = order.symbol
        
        # 检查是否是我们跟踪的交易
        if 股票代码 not in self.交易状态:
            return
        
        交易状态 = self.交易状态[股票代码]
        
        # 处理卖出订单取消
        if order.direction == Direction.SHORT and 交易状态.get("状态") == "卖出中":
            self.write_log(f"卖出订单被取消: {股票代码}")
            self._清理交易状态(股票代码)
        
        # 处理买入订单取消
        elif order.direction == Direction.LONG:
            if 交易状态.get("状态") == "买回中":
                # 买回订单被取消，可能需要重新买回
                self.write_log(f"买回订单被取消: {股票代码}, 尝试重新买回")
                
                # 获取当前市场价格
                市场数据 = self.get_tick(f"{股票代码}.{self._判断交易所(股票代码).value}")
                
                if 市场数据:
                    买回价格 = 市场数据.bid_price_1  # 使用买一价
                    买回数量 = 交易状态["卖出数量"]
                    
                    # 发送新的买入订单
                    交易所 = self._判断交易所(股票代码)
                    vt_symbol = f"{股票代码}.{交易所.value}"
                    
                    order_id = self.buy(vt_symbol, 买回价格, 买回数量)
                    
                    if order_id:
                        交易状态["买入订单ID"] = order_id
                        交易状态["买入价格"] = 买回价格
                    else:
                        # 买回失败，记录风险
                        self.write_log(f"重新买回失败: {股票代码}")
                else:
                    self.write_log(f"无法获取市场数据: {股票代码}")
            
            elif 交易状态.get("状态") == "建仓中":
                # 建仓订单被取消
                self.write_log(f"建仓订单被取消: {股票代码}")
                self._清理交易状态(股票代码)
    
    def _清理交易状态(self, 股票代码: str):
        """
        清理指定股票的交易状态
        
        参数:
            股票代码: 股票代码
        """
        if 股票代码 in self.交易状态:
            # 保存交易记录
            记录 = self.交易状态[股票代码].copy()
            记录["结束时间"] = datetime.now()
            
            # 添加到交易记录
            self._保存单笔交易记录(记录)
            
            # 删除交易状态
            del self.交易状态[股票代码]
    
    def _保存单笔交易记录(self, 记录: Dict):
        """
        保存单笔交易记录
        
        参数:
            记录: 交易记录
        """
        # 构建文件路径
        日期 = datetime.now().strftime("%Y%m%d")
        文件路径 = f"{self.数据路径}交易记录_{日期}.json"
        
        # 读取现有记录
        交易记录 = []
        if os.path.exists(文件路径):
            try:
                with open(文件路径, "r", encoding="utf-8") as f:
                    交易记录 = json.load(f)
            except:
                pass
        
        # 添加新记录
        交易记录.append(记录)
        
        # 保存记录
        with open(文件路径, "w", encoding="utf-8") as f:
            json.dump(交易记录, f, indent=4, ensure_ascii=False, default=self._json序列化处理)
    
    def _保存交易记录(self):
        """保存所有交易记录和统计数据"""
        # 导出风控日志
        风控日志 = self.风险控制.导出风控日志()
        日期 = datetime.now().strftime("%Y%m%d")
        风控文件路径 = f"{self.数据路径}风控日志_{日期}.json"
        
        with open(风控文件路径, "w", encoding="utf-8") as f:
            json.dump(风控日志, f, indent=4, ensure_ascii=False, default=self._json序列化处理)
        
        # 导出资金统计
        资金统计 = self.资金管理.获取每日统计()
        统计文件路径 = f"{self.数据路径}资金统计_{日期}.json"
        
        with open(统计文件路径, "w", encoding="utf-8") as f:
            json.dump(资金统计, f, indent=4, ensure_ascii=False, default=self._json序列化处理)
    
    def _json序列化处理(self, obj):
        """处理无法序列化的对象"""
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S.%f")
        return str(obj)

    def _处理大象消失(self, 股票代码: str, 盘口数据: Dict):
        """
        处理大象消失事件
        
        参数:
            股票代码: 股票代码
            盘口数据: 盘口数据
        """
        if 股票代码 not in self.交易状态:
            return
            
        交易状态 = self.交易状态[股票代码]
        大象信息 = 交易状态.get("大象信息", {})
        大象类型 = 大象信息.get("类型", "")
        
        # 根据不同的大象类型和交易状态处理
        if "买单大象" in 大象类型:
            # 下方大象消失处理
            if 交易状态.get("状态") == "持有中":
                # 如果持有股票但还没卖出，需要紧急止损
                self.write_log(f"下方大象消失，执行止损: {股票代码}")
                
                交易所 = self._判断交易所(股票代码)
                vt_symbol = f"{股票代码}.{交易所.value}"
                
                # 以当前市场价格止损卖出
                if 盘口数据 and 盘口数据.get("bids") and 盘口数据["bids"][0]:
                    买一价 = 盘口数据["bids"][0][0]
                    卖出数量 = 交易状态.get("买入成交数量", 0)
                    
                    if 卖出数量 > 0:
                        order_id = self.sell(vt_symbol, 买一价, 卖出数量)
                        
                        if order_id:
                            交易状态.update({
                                "状态": "止损中",
                                "卖出订单ID": order_id,
                                "卖出价格": 买一价,
                                "卖出数量": 卖出数量
                            })
                            self.write_log(f"下方大象消失止损卖出: {股票代码} {卖出数量}股 @ {买一价}")
                        else:
                            self.write_log(f"下方大象消失止损卖出失败: {股票代码}")
        
        elif "卖单大象" in 大象类型:
            # 上方大象消失处理
            if 交易状态.get("状态") == "已卖出待买回":
                # 如果已卖出但还没买回，需要紧急买回
                self.write_log(f"上方大象消失，执行紧急买回: {股票代码}")
                
                交易所 = self._判断交易所(股票代码)
                vt_symbol = f"{股票代码}.{交易所.value}"
                
                # 以当前市场价格紧急买回
                if 盘口数据 and 盘口数据.get("asks") and 盘口数据["asks"][0]:
                    卖一价 = 盘口数据["asks"][0][0]
                    买回数量 = 交易状态.get("卖出成交数量", 0)
                    
                    if 买回数量 > 0:
                        order_id = self.buy(vt_symbol, 卖一价, 买回数量)
                        
                        if order_id:
                            交易状态.update({
                                "状态": "紧急买回中",
                                "买入订单ID": order_id,
                                "买入价格": 卖一价,
                                "买入数量": 买回数量
                            })
                            self.write_log(f"上方大象消失紧急买回: {股票代码} {买回数量}股 @ {卖一价}")
                        else:
                            self.write_log(f"上方大象消失紧急买回失败: {股票代码}")

    def _运行测试(self):
        """运行策略模块测试"""
        self.write_log("开始运行策略模块测试")
        
        try:
            # 运行所有测试
            测试结果 = 运行所有测试()
            
            # 记录测试结果
            测试成功率 = 测试结果["成功率"] * 100
            self.write_log(f"测试完成，成功率: {测试成功率:.2f}%")
            self.write_log(f"测试总数: {测试结果['测试总数']}, 成功: {测试结果['成功数']}, 失败: {测试结果['失败数']}, 错误: {测试结果['错误数']}")
            
            # 如果有网页管理器，记录测试结果
            if self.网页管理:
                self.网页管理.记录日志(f"模块测试完成，成功率: {测试成功率:.2f}%")
            
            return 测试结果
        except Exception as e:
            错误信息 = f"运行测试时出错: {str(e)}"
            self.write_log(错误信息)
            if self.网页管理:
                self.网页管理.记录日志(错误信息)
            return None 

    def _写入日志文件(self, msg):
        """将日志写入文件"""
        try:
            if hasattr(self, "交易日志文件路径") and self.交易日志文件路径:
                时间 = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                with open(self.交易日志文件路径, "a", encoding="utf-8") as f:
                    f.write(f"{时间},[INFO],{msg}\n")
        except Exception as e:
            # 如果写入失败，直接打印到控制台
            print(f"写入日志文件失败: {e} - 原始消息: {msg}")
            
    def _初始化交易日志文件(self):
        """初始化交易日志文件"""
        try:
            日志目录 = os.path.dirname(self.交易日志文件路径)
            if not os.path.exists(日志目录):
                os.makedirs(日志目录, exist_ok=True)
                
            with open(self.交易日志文件路径, "w", encoding="utf-8") as f:
                f.write("时间,级别,消息\n")
            print(f"初始化交易日志文件: {self.交易日志文件路径}")
        except Exception as e:
            print(f"初始化交易日志文件失败: {e}")
            
            # 尝试在当前目录创建日志文件
            self.交易日志文件路径 = f"大象策略日志_{datetime.now().strftime('%Y%m%d')}.log"
            try:
                with open(self.交易日志文件路径, "w", encoding="utf-8") as f:
                    f.write("时间,级别,消息\n")
                print(f"在当前目录初始化交易日志文件: {self.交易日志文件路径}")
            except Exception as e2:
                print(f"在当前目录初始化交易日志文件也失败: {e2}")
                # 禁用日志记录
                self.启用详细交易日志 = False

    def _记录交易日志(self, 日志数据: dict):
        """
        记录交易日志到文件
        
        参数:
            日志数据: 交易日志数据
        """
        if not self.启用详细交易日志:
            return
            
        try:
            当前时间 = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            股票代码 = 日志数据.get("股票代码", "")
            交易类型 = 日志数据.get("类型", "")  # 下方大象策略或上方大象策略
            操作 = 日志数据.get("操作", "")  # 买入、卖出、买回等
            价格 = 日志数据.get("价格", 0)
            数量 = 日志数据.get("数量", 0)
            状态 = 日志数据.get("状态", "")
            大象类型 = 日志数据.get("大象类型", "")
            大象价格 = 日志数据.get("大象价格", 0)
            大象金额 = 日志数据.get("大象金额", 0)
            
            日志行 = f"{当前时间},{股票代码},{交易类型},{操作},{价格},{数量},{状态},{大象类型},{大象价格},{大象金额}\n"
            
            with open(self.交易日志文件路径, "a", encoding="utf-8") as f:
                f.write(日志行)
        except Exception as e:
            self.write_log(f"记录交易日志错误: {e}")

    def _更新最新价格(self, 股票代码: str, 价格: float):
        """
        更新股票最新价格
        
        参数:
            股票代码: 股票代码
            价格: 最新价格
        """
        # 这里可以添加价格存储逻辑，目前先简单记录即可
        # 如果需要保存价格历史，可以使用字典存储
        if not hasattr(self, "_最新价格"):
            self._最新价格 = {}
        
        self._最新价格[股票代码] = 价格

    def write_log(self, msg: str):
        """
        写入日志
        
        参数:
            msg: 日志信息
        """
        try:
            if self.cta_engine:
                self.cta_engine.write_log(msg, self.strategy_name)
            else:
                # 如果cta_engine不可用，则直接打印到控制台
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [INFO] {self.strategy_name}: {msg}")
                
            # 将日志写入日志文件
            if hasattr(self, "启用详细交易日志") and self.启用详细交易日志:
                self._写入日志文件(msg)
        except Exception as e:
            # 如果log失败，确保不影响主程序
            print(f"日志记录失败: {e} - 原始消息: {msg}")