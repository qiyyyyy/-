#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大象策略主文件 - 基于vnpy的高频大象策略
适用于中国A股T+1市场，使用一半现金一半股票的资金配置

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
from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager,
    StopOrder
)

# 导入策略模块
from modules.资金管理 import 资金管理器
from modules.大象识别 import 大象识别器
from modules.交易执行 import 交易执行器
from modules.风险控制 import 风险控制器
from modules.网页管理 import 网页管理器
from modules.测试模块 import 测试管理器, 运行所有测试


class 大象策略(CtaTemplate):
    """
    大象策略主类 - 基于先卖后买的高频交易策略
    
    策略思路：
    1. 识别盘口中的大单买盘支撑（大象）
    2. 利用已持有的股票进行"先卖后买"的高频交易
    3. 同时使用现金部分适时建立新的仓位，以维持资金平衡
    """
    
    # 策略作者
    author = "AI助手"
    
    # 策略参数
    # 大象识别参数
    大象委托量阈值 = 1000000.0  # 判定为大象的最小委托量(元)
    大象价差阈值 = 0.05  # 大象与卖一价的最大价差(%)
    大象确认次数 = 3  # 确认大象存在的检测次数
    大象稳定时间 = 5  # 大象稳定存在的最小秒数
    
    # 交易执行参数
    价格偏移量 = 0.01  # 最小价格变动单位
    卖出偏移量倍数 = 2.0  # 卖出价高于大象价格的偏移量倍数
    买入偏移量倍数 = 1.0  # 买入价高于大象价格的偏移量倍数
    等待时间 = 30  # 等待订单成交的最长时间(秒)
    冷却时间 = 300  # 同一股票交易后的冷却时间(秒)
    止损价格比例 = 0.5  # 相对于大象价差的止损比例
    
    # 资金管理参数
    股票池比例 = 0.5  # 股票资金池目标比例
    买回保障金比例 = 0.7  # 现金池中作为买回保障的比例
    单股最大仓位比例 = 0.1  # 单只股票最大持仓占总资产比例
    
    # 风险控制参数
    单笔最大亏损比例 = 0.001  # 单笔交易最大亏损占总资产比例
    单股最大亏损比例 = 0.005  # 单只股票日内最大亏损占总资产比例
    日内最大亏损比例 = 0.01  # 日内最大总亏损占总资产比例
    单股最大交易次数 = 10  # 单只股票日内最大交易次数
    总交易次数限制 = 100  # 日内总交易次数限制
    
    # 网页管理参数
    启用网页管理 = True  # 是否启用网页管理
    网页管理端口 = 8088  # 网页管理端口
    自动打开浏览器 = True  # 是否自动打开浏览器
    
    # 跟踪持仓股票列表
    交易股票列表 = []  # 要交易的股票列表
    
    # 变量
    交易状态 = {}  # 各股票交易状态
    
    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """初始化大象策略"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        # 初始化各个模块
        self.资金管理 = 资金管理器(
            初始资产=0,
            股票池比例=self.股票池比例,
            买回保障金比例=self.买回保障金比例
        )
        
        self.大象识别 = 大象识别器(
            大象委托量阈值=self.大象委托量阈值,
            大象价差阈值=self.大象价差阈值,
            确认次数=self.大象确认次数,
            大象稳定时间=self.大象稳定时间
        )
        
        self.交易执行 = 交易执行器(
            价格偏移量=self.价格偏移量,
            卖出偏移量倍数=self.卖出偏移量倍数,
            买入偏移量倍数=self.买入偏移量倍数,
            等待时间=self.等待时间,
            冷却时间=self.冷却时间,
            止损价格比例=self.止损价格比例
        )
        
        self.风险控制 = 风险控制器(
            单笔最大亏损比例=self.单笔最大亏损比例,
            单股最大亏损比例=self.单股最大亏损比例,
            日内最大亏损比例=self.日内最大亏损比例,
            单股最大交易次数=self.单股最大交易次数,
            总交易次数限制=self.总交易次数限制
        )
        
        # 初始化网页管理器
        self.网页管理 = None
        if self.启用网页管理:
            self.网页管理 = 网页管理器(
                端口=self.网页管理端口,
                自动打开浏览器=self.自动打开浏览器
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
            self.write_log(f"网页管理服务已启动，端口:{self.网页管理端口}")
    
    def on_start(self):
        """策略启动"""
        self.write_log("策略启动")
        self.策略状态 = "运行中"
        
        # 更新资产状态
        self._更新账户信息()
        
        # 检查未完成订单
        self._检查未完成订单()
        
        # 可以在这里运行测试
        # self._运行测试()
    
    def on_stop(self):
        """策略停止"""
        self.write_log("策略停止")
        self.策略状态 = "已停止"
        
        # 取消所有活跃订单
        self._取消所有活跃订单()
        
        # 保存交易记录
        self._保存交易记录()
        
        # 停止网页管理器
        if self.网页管理 and self.网页管理.运行中:
            self.网页管理.停止()
            self.write_log("网页管理服务已停止")
    
    def on_tick(self, tick: TickData):
        """
        行情数据更新回调
        
        参数:
            tick: 最新行情数据
        """
        # 提取股票代码
        股票代码 = tick.symbol
        
        # 构建盘口深度数据
        盘口数据 = {
            "bids": [
                [tick.bid_price_1, tick.bid_volume_1],
                [tick.bid_price_2, tick.bid_volume_2],
                [tick.bid_price_3, tick.bid_volume_3],
                [tick.bid_price_4, tick.bid_volume_4],
                [tick.bid_price_5, tick.bid_volume_5]
            ],
            "asks": [
                [tick.ask_price_1, tick.ask_volume_1],
                [tick.ask_price_2, tick.ask_volume_2],
                [tick.ask_price_3, tick.ask_volume_3],
                [tick.ask_price_4, tick.ask_volume_4],
                [tick.ask_price_5, tick.ask_volume_5]
            ]
        }
        
        # 检测大象
        当前时间 = datetime.now()
        大象信息 = self.大象识别.检测大象(股票代码, 盘口数据, 当前时间)
        
        # 如果存在大象，尝试交易
        if 大象信息 and 股票代码 in self.交易股票列表:
            self._处理大象交易信号(股票代码, 大象信息, 盘口数据)
        
        # 检查大象是否消失，如果消失则执行风险控制
        if 股票代码 in self.交易状态 and self.交易状态[股票代码].get("状态") == "卖出待买回":
            if self.大象识别.检查大象是否消失(股票代码, 盘口数据):
                self._处理大象消失(股票代码, 盘口数据)
    
    def on_bar(self, bar: BarData):
        """
        K线数据更新回调
        
        参数:
            bar: 最新K线数据
        """
        # K线数据可用于分析趋势，暂不使用
        pass
    
    def on_order(self, order: OrderData):
        """
        订单状态更新回调
        
        参数:
            order: 订单数据
        """
        # 更新订单状态
        self.write_log(f"订单状态更新: {order.symbol}, {order.direction}, {order.status}")
        
        # 处理订单完成事件
        if order.status == Status.ALLTRADED:
            self._处理订单完成(order)
        elif order.status in [Status.CANCELLED, Status.REJECTED]:
            self._处理订单取消(order)
    
    def on_trade(self, trade: TradeData):
        """
        成交更新回调
        
        参数:
            trade: 成交数据
        """
        # 更新成交记录
        self.write_log(f"成交: {trade.symbol}, {trade.direction}, 价格: {trade.price}, 数量: {trade.volume}")
        
        # 更新资金管理模块中的持仓
        是买入 = trade.direction == Direction.LONG
        self.资金管理.更新持仓(trade.symbol, trade.volume, trade.price, 是买入)
    
    def on_timer(self, event):
        """
        定时器回调
        
        参数:
            event: 事件数据
        """
        # 每分钟执行一次检查
        当前时间 = datetime.now()
        if not self.上次检查时间 or (当前时间 - self.上次检查时间).total_seconds() >= 60:
            # 更新账户信息
            self._更新账户信息()
            
            # 检查风控状态，必要时重置
            self.风险控制.检查并重置风控状态()
            
            # 清理过期数据
            self.交易执行.清理过期数据()
            
            # 更新上次检查时间
            self.上次检查时间 = 当前时间
    
    def _加载交易股票(self):
        """加载要交易的股票列表"""
        try:
            # 尝试从配置文件加载
            配置文件 = "config/stocks.json"
            if os.path.exists(配置文件):
                with open(配置文件, "r", encoding="utf-8") as f:
                    数据 = json.load(f)
                    self.交易股票列表 = 数据.get("stocks", [])
                    self.write_log(f"从配置文件加载交易股票列表，共{len(self.交易股票列表)}只")
            else:
                # 如果配置文件不存在，使用当前持仓作为交易股票
                self.write_log("配置文件不存在，将使用当前持仓作为交易股票")
                self._更新交易股票列表()
        except Exception as e:
            self.write_log(f"加载交易股票列表出错: {e}")
            self._更新交易股票列表()
    
    def _更新交易股票列表(self):
        """根据当前持仓更新交易股票列表"""
        positions = self.cta_engine.main_engine.get_all_positions()
        持仓股票 = [position.symbol for position in positions if position.volume > 0]
        
        self.交易股票列表 = 持仓股票
        self.write_log(f"更新交易股票列表，共{len(self.交易股票列表)}只")
        
        # 保存到配置文件
        配置文件 = "config/stocks.json"
        os.makedirs(os.path.dirname(配置文件), exist_ok=True)
        with open(配置文件, "w", encoding="utf-8") as f:
            json.dump({"stocks": self.交易股票列表}, f, indent=4, ensure_ascii=False)
    
    def _订阅股票行情(self):
        """订阅交易股票的行情"""
        for 股票代码 in self.交易股票列表:
            if 股票代码 not in self.已订阅股票:
                交易所 = self._判断交易所(股票代码)
                vt_symbol = f"{股票代码}.{交易所.value}"
                
                self.cta_engine.subscribe(vt_symbol)
                self.已订阅股票.add(股票代码)
                self.write_log(f"订阅行情: {vt_symbol}")
    
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
    
    def _检查未完成订单(self):
        """检查未完成订单，必要时取消"""
        orders = self.cta_engine.main_engine.get_all_active_orders()
        
        if orders:
            self.write_log(f"发现{len(orders)}个未完成订单，尝试取消")
            for order in orders:
                self.cancel_order(order.vt_orderid)
    
    def _取消所有活跃订单(self):
        """取消所有活跃订单"""
        orders = self.cta_engine.main_engine.get_all_active_orders()
        
        if orders:
            self.write_log(f"取消{len(orders)}个活跃订单")
            for order in orders:
                self.cancel_order(order.vt_orderid)
    
    def _处理大象交易信号(self, 股票代码: str, 大象信息: Dict, 盘口数据: Dict):
        """
        处理大象交易信号
        
        参数:
            股票代码: 股票代码
            大象信息: 大象信息
            盘口数据: 盘口深度数据
        """
        # 检查该股票是否在交易中
        if 股票代码 in self.交易状态 and self.交易状态[股票代码].get("状态") != "空闲":
            return
        
        # 检查是否在交易冷却期
        if not self.交易执行.检查交易冷却期(股票代码):
            return
        
        # 检查大象稳定性
        if not self.大象识别.检查大象稳定性(股票代码):
            return
        
        # 获取可卖出数量
        可卖出数量 = self.资金管理.获取可卖出数量(股票代码)
        if 可卖出数量 <= 0:
            # 如果没有持仓，尝试建立新仓位
            self._尝试建立新仓位(股票代码, 大象信息)
            return
        
        # 计算交易数量（取整百股）
        交易价格 = self.交易执行.计算卖出价格(大象信息)
        交易金额 = 交易价格 * 可卖出数量
        
        # 计算潜在亏损（假设最坏情况）
        最差买回价格 = 大象信息["卖一价"]  # 最坏情况下，可能要以卖一价买回
        最大亏损 = (最差买回价格 - 交易价格) * 可卖出数量
        
        # 检查风险
        允许交易, 拒绝原因 = self.风险控制.检查交易风险(股票代码, 最大亏损)
        if not 允许交易:
            self.write_log(f"风险控制拒绝交易 {股票代码}: {拒绝原因}")
            return
        
        # 定义交易数量，不超过持仓
        交易数量 = min(可卖出数量, 1000)  # 初始化为最多1000股
        
        # 确保交易数量为100的整数倍
        交易数量 = int(交易数量 / 100) * 100
        
        # 如果交易数量太小，不执行交易
        if 交易数量 < 100:
            return
        
        # 执行卖出操作
        self.write_log(f"执行大象交易: {股票代码}, 价格: {交易价格}, 数量: {交易数量}")
        
        # 记录交易状态
        self.交易状态[股票代码] = {
            "状态": "卖出中",
            "大象信息": 大象信息,
            "卖出价格": 交易价格,
            "卖出数量": 交易数量,
            "开始时间": datetime.now()
        }
        
        # 发送卖出订单
        交易所 = self._判断交易所(股票代码)
        vt_symbol = f"{股票代码}.{交易所.value}"
        order_id = self.sell(vt_symbol, 交易价格, 交易数量)
        
        # 记录订单ID
        if order_id:
            self.交易状态[股票代码]["卖出订单ID"] = order_id
    
    def _尝试建立新仓位(self, 股票代码: str, 大象信息: Dict):
        """
        尝试使用现金池建立新仓位
        
        参数:
            股票代码: 股票代码
            大象信息: 大象信息
        """
        # 检查是否有可用现金
        可用资金 = self.资金管理.获取可建仓资金()
        if 可用资金 <= 0:
            return
        
        # 计算买入价格和数量
        买入价格 = self.交易执行.计算买入价格(大象信息)
        最大交易数量 = self.资金管理.计算建仓数量(股票代码, 买入价格, self.单股最大仓位比例)
        
        # 确保交易数量为100的整数倍
        交易数量 = int(最大交易数量 / 100) * 100
        
        # 如果交易数量太小，不执行交易
        if 交易数量 < 100:
            return
        
        # 检查风险
        允许交易, 拒绝原因 = self.风险控制.检查交易风险(股票代码)
        if not 允许交易:
            self.write_log(f"风险控制拒绝建仓 {股票代码}: {拒绝原因}")
            return
        
        # 执行买入操作
        self.write_log(f"建立新仓位: {股票代码}, 价格: {买入价格}, 数量: {交易数量}")
        
        # 记录交易状态
        self.交易状态[股票代码] = {
            "状态": "建仓中",
            "大象信息": 大象信息,
            "买入价格": 买入价格,
            "买入数量": 交易数量,
            "开始时间": datetime.now()
        }
        
        # 发送买入订单
        交易所 = self._判断交易所(股票代码)
        vt_symbol = f"{股票代码}.{交易所.value}"
        order_id = self.buy(vt_symbol, 买入价格, 交易数量)
        
        # 记录订单ID
        if order_id:
            self.交易状态[股票代码]["买入订单ID"] = order_id
    
    def _处理大象消失(self, 股票代码: str, 盘口数据: Dict):
        """
        处理大象消失情况
        
        参数:
            股票代码: 股票代码
            盘口数据: 盘口深度数据
        """
        if 股票代码 not in self.交易状态 or self.交易状态[股票代码].get("状态") != "卖出待买回":
            return
        
        # 获取交易状态
        交易状态 = self.交易状态[股票代码]
        
        # 如果已经发送了买回订单，不再处理
        if "买入订单ID" in 交易状态:
            return
        
        # 确定买回价格和数量
        买回数量 = 交易状态["卖出数量"]
        
        # 使用当前买一价作为紧急买回价格
        买回价格 = 盘口数据["bids"][0][0] if len(盘口数据["bids"]) > 0 else None
        
        if not 买回价格:
            self.write_log(f"无法获取 {股票代码} 的买回价格")
            return
        
        self.write_log(f"大象消失，执行紧急买回: {股票代码}, 价格: {买回价格}, 数量: {买回数量}")
        
        # 发送买入订单
        交易所 = self._判断交易所(股票代码)
        vt_symbol = f"{股票代码}.{交易所.value}"
        order_id = self.buy(vt_symbol, 买回价格, 买回数量)
        
        # 记录订单ID
        if order_id:
            self.交易状态[股票代码]["买入订单ID"] = order_id
            self.交易状态[股票代码]["状态"] = "买回中"
            self.交易状态[股票代码]["买入价格"] = 买回价格
    
    def _处理订单完成(self, order: OrderData):
        """
        处理订单完成
        
        参数:
            order: 订单数据
        """
        股票代码 = order.symbol
        
        # 检查是否是我们跟踪的交易
        if 股票代码 not in self.交易状态:
            return
        
        交易状态 = self.交易状态[股票代码]
        
        # 处理卖出订单完成
        if order.direction == Direction.SHORT and 交易状态.get("状态") == "卖出中":
            # 更新交易状态
            交易状态["状态"] = "卖出待买回"
            交易状态["实际卖出价格"] = order.price
            
            # 计算买回价格
            大象信息 = 交易状态["大象信息"]
            买回价格 = self.交易执行.计算买入价格(大象信息)
            
            # 发送买入订单
            交易所 = self._判断交易所(股票代码)
            vt_symbol = f"{股票代码}.{交易所.value}"
            买回数量 = 交易状态["卖出数量"]
            
            self.write_log(f"卖出完成，发送买回订单: {股票代码}, 价格: {买回价格}, 数量: {买回数量}")
            
            order_id = self.buy(vt_symbol, 买回价格, 买回数量)
            
            # 记录订单ID
            if order_id:
                交易状态["买入订单ID"] = order_id
                交易状态["买入价格"] = 买回价格
                交易状态["状态"] = "买回中"
        
        # 处理买入订单完成
        elif order.direction == Direction.LONG:
            if 交易状态.get("状态") in ["买回中", "卖出待买回"]:
                # 高频交易的买回完成
                交易状态["状态"] = "已完成"
                交易状态["实际买入价格"] = order.price
                
                # 计算盈亏
                卖出价格 = 交易状态.get("实际卖出价格", 交易状态["卖出价格"])
                买入价格 = order.price
                交易数量 = 交易状态["卖出数量"]
                盈亏 = (卖出价格 - 买入价格) * 交易数量
                
                # 记录交易盈亏
                self.风险控制.记录交易盈亏(股票代码, 盈亏)
                
                self.write_log(f"高频交易完成: {股票代码}, 盈亏: {盈亏:.2f}")
                
                # 清理交易状态
                self._清理交易状态(股票代码)
            
            elif 交易状态.get("状态") == "建仓中":
                # 建仓完成
                交易状态["状态"] = "已完成"
                交易状态["实际买入价格"] = order.price
                
                self.write_log(f"建仓完成: {股票代码}, 价格: {order.price}, 数量: {order.volume}")
                
                # 清理交易状态
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