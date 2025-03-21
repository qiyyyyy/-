"""
Trading strategy implementation
"""
import time
import asyncio
import uuid
from typing import Dict, List, Optional
import ccxt.async_support as ccxt  # 修改为使用异步支持版本
from decimal import Decimal, ROUND_DOWN
from .utils import Logger, DataProcessor, RiskManager, DataStorage, PerformanceMonitor, handle_api_error
from datetime import datetime as dt
import os
import random
import platform

class HighFrequencyStrategy:
    def __init__(self, exchange_config: Dict, trading_config: Dict, strategy_config: Dict):
        # 保存配置
        self.exchange_config = exchange_config
        self.trading_config = trading_config
        self.strategy_config = strategy_config
        
        # 初始化日志记录器
        # 使用相同的日志目录
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # 创建带时间戳的日志文件名
        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(logs_dir, f'strategy_{timestamp}.log')
        
        self.logger = Logger('HighFrequencyStrategy', log_file=log_file)
        
        # 创建交易所实例
        exchange_id = exchange_config.get('exchange', 'binance')
        self.exchange = getattr(ccxt, exchange_id)(exchange_config)
        
        # 初始化数据处理和风险管理
        self.data_processor = DataProcessor()
        self.risk_manager = RiskManager(trading_config)
        self.data_storage = DataStorage()
        
        # 任务队列
        self.tasks = []
        self.pending_orders = {}
        
        # 性能监控
        self.latency_metrics = {
            'order_latency': [],
            'market_data_latency': [],
            'cycle_latency': []
        }
        
        # 初始化市场数据
        self.market_data = {}
        for symbol in trading_config['symbols']:
            self.market_data[symbol] = {
                'trades': [],
                'buy_trades': [],  # 买单成交
                'sell_trades': [], # 卖单成交
                'orderbook': None,
                'position': None,
                'last_update': 0,
                'avg_spread': 0,   # 平均价差
                'buy_metrics': {   # 买单指标
                    'avg_price': 0,
                    'last_price': 0,
                    'avg_amount': 0,
                    'avg_frequency': 0,
                },
                'sell_metrics': {  # 卖单指标
                    'avg_price': 0,
                    'last_price': 0,
                    'avg_amount': 0,
                    'avg_frequency': 0,
                }
            }
        
        # 标记初始化状态
        self.initialized = False
    
    async def initialize(self):
        """初始化策略"""
        self.logger.info("正在初始化策略...")
        
        try:
            # 如果是Windows系统，使用SelectorEventLoop
            if platform.system() == 'Windows':
                import asyncio
                import selectors
                # 解决Windows上的aiodns问题
                try:
                    self.logger.info("检测到Windows系统，设置SelectorEventLoop")
                    selector = selectors.SelectSelector()
                    loop = asyncio.SelectorEventLoop(selector)
                    asyncio.set_event_loop(loop)
                except Exception as e:
                    self.logger.warning(f"设置Windows事件循环失败: {str(e)}")
            
            # 如果启用了测试网，使用测试网
            if self.exchange_config.get('testnet', False):
                self.exchange.set_sandbox_mode(True)
                self.logger.info(f"已启用测试网环境: {self.exchange.id}")
            
            # 测试API连接并验证权限
            try:
                self.logger.info("验证API连接...")
                max_retries = 3
                retry_count = 0
                balance = None
                
                while retry_count < max_retries:
                    try:
                        balance = await self.exchange.fetch_balance()
                        break  # 成功则跳出循环
                    except Exception as retry_error:
                        retry_count += 1
                        error_msg = str(retry_error)
                        
                        if 'aiodns needs a SelectorEventLoop on Windows' in error_msg:
                            self.logger.error(f"Windows aiodns错误: {error_msg}")
                            # 尝试修复Windows上的aiodns问题
                            import asyncio
                            import selectors
                            try:
                                selector = selectors.SelectSelector()
                                loop = asyncio.SelectorEventLoop(selector)
                                asyncio.set_event_loop(loop)
                                self.logger.info("尝试重新设置Windows事件循环")
                            except Exception as loop_error:
                                self.logger.error(f"重新设置事件循环失败: {str(loop_error)}")
                        
                        if retry_count < max_retries:
                            self.logger.warning(f"API连接失败，重试 {retry_count}/{max_retries}")
                            await asyncio.sleep(1)
                        else:
                            await handle_api_error(
                                retry_error, self.exchange.id, "验证API连接",
                                self.exchange.fetch_balance
                            )
                            raise Exception(f"API连接验证失败: {str(retry_error)}")
                
                if balance:
                    self.logger.info(f"API连接成功，可用余额: {balance['free']}")
                
                # 测试设置杠杆 (Binance期货特有)
                if self.exchange.id.lower() == 'binance' and self.exchange_config.get('options', {}).get('defaultType') == 'future':
                    for symbol in self.trading_config['symbols']:
                        try:
                            self.logger.info(f"设置{symbol}杠杆...")
                            await self.exchange.set_leverage(1, symbol)
                            self.logger.info(f"已设置{symbol}杠杆为1")
                        except Exception as e:
                            error_msg = str(e)
                            await handle_api_error(
                                e, self.exchange.id, f"设置{symbol}杠杆为1",
                                self.exchange.set_leverage, (1, symbol)
                            )
                
            except Exception as api_error:
                # 使用新增的API错误处理函数
                await handle_api_error(
                    api_error, self.exchange.id, "验证API连接",
                    self.exchange.fetch_balance
                )
                raise Exception(f"API连接验证失败: {str(api_error)}")
            
            # 加载市场数据
            await self.exchange.load_markets()
            self.logger.info(f"已加载{len(self.exchange.markets)}个市场")
            
            # 初始化性能监控
            self.performance_monitor = PerformanceMonitor()
            
            self.initialized = True
            self.logger.info("策略初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化策略失败: {str(e)}")
            if hasattr(self, 'exchange') and self.exchange:
                await self.exchange.close()
            raise e
    
    async def update_market_data(self, symbol: str):
        """更新市场数据"""
        start_time = time.time()
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 获取最新成交
                trades = await self.exchange.fetch_trades(symbol)
                self.market_data[symbol]['trades'] = trades
                
                # 分离买卖单成交
                buy_trades = [t for t in trades if t['side'] == 'buy']
                sell_trades = [t for t in trades if t['side'] == 'sell']
                
                self.market_data[symbol]['buy_trades'] = buy_trades
                self.market_data[symbol]['sell_trades'] = sell_trades
                
                # 获取订单簿
                orderbook = await self.exchange.fetch_order_book(symbol)
                self.market_data[symbol]['orderbook'] = orderbook
                
                # 获取持仓信息
                positions = await self.exchange.fetch_positions([symbol])
                for position in positions:
                    if position['symbol'] == symbol:
                        self.market_data[symbol]['position'] = position
                        break
                
                # 计算交易指标
                await self._calculate_trade_metrics(symbol)
                
                # 记录延迟
                self.market_data[symbol]['last_update'] = time.time()
                self.latency_metrics['market_data_latency'].append(time.time() - start_time)
                
                # 成功获取数据，退出重试循环
                return
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if "502 Bad Gateway" in error_msg:
                    if retry_count < max_retries:
                        self.logger.warning(f"Received 502 Bad Gateway when updating market data for {symbol}, retry {retry_count}/{max_retries}")
                        await asyncio.sleep(retry_count)  # 增加退避时间
                    else:
                        self.logger.error(f"Failed to update market data for {symbol} after {max_retries} retries: {error_msg}")
                else:
                    self.logger.error(f"Failed to update market data for {symbol}: {error_msg}")
                    break  # 对于非502错误，不进行重试
        
        # 如果所有重试都失败，但我们已经有一些市场数据，标记为旧数据但不完全清除
        if symbol in self.market_data:
            current_time = time.time()
            last_update = self.market_data[symbol].get('last_update', 0)
            
            # 如果数据超过5分钟未更新，标记为过期
            if current_time - last_update > 300:
                self.logger.warning(f"Market data for {symbol} is stale (>5min old)")
    
    async def _calculate_trade_metrics(self, symbol: str):
        """计算交易指标"""
        market_data = self.market_data[symbol]
        volume_window = self.strategy_config['volume_window']
        price_window = self.strategy_config['price_window']
        
        # 计算买单指标
        buy_trades = market_data['buy_trades']
        if buy_trades:
            # 过滤时间窗口内的交易
            now = time.time()
            window_buy_trades = [t for t in buy_trades if now - t['timestamp']/1000 <= volume_window]
            
            if window_buy_trades:
                # 平均价格
                avg_buy_price = sum([t['price'] for t in window_buy_trades]) / len(window_buy_trades)
                # 最新价格
                last_buy_price = window_buy_trades[-1]['price']
                # 平均成交量
                avg_buy_amount = sum([t['amount'] for t in window_buy_trades]) / len(window_buy_trades)
                # 交易频率 (每秒交易次数)
                if len(window_buy_trades) > 1:
                    time_span = window_buy_trades[-1]['timestamp']/1000 - window_buy_trades[0]['timestamp']/1000
                    if time_span > 0:
                        frequency = len(window_buy_trades) / time_span
                    else:
                        frequency = 1  # 默认值
                else:
                    frequency = 1  # 默认值
                
                market_data['buy_metrics'] = {
                    'avg_price': avg_buy_price,
                    'last_price': last_buy_price,
                    'avg_amount': avg_buy_amount,
                    'avg_frequency': frequency
                }
        
        # 计算卖单指标
        sell_trades = market_data['sell_trades']
        if sell_trades:
            # 过滤时间窗口内的交易
            now = time.time()
            window_sell_trades = [t for t in sell_trades if now - t['timestamp']/1000 <= volume_window]
            
            if window_sell_trades:
                # 平均价格
                avg_sell_price = sum([t['price'] for t in window_sell_trades]) / len(window_sell_trades)
                # 最新价格
                last_sell_price = window_sell_trades[-1]['price']
                # 平均成交量
                avg_sell_amount = sum([t['amount'] for t in window_sell_trades]) / len(window_sell_trades)
                # 交易频率 (每秒交易次数)
                if len(window_sell_trades) > 1:
                    time_span = window_sell_trades[-1]['timestamp']/1000 - window_sell_trades[0]['timestamp']/1000
                    if time_span > 0:
                        frequency = len(window_sell_trades) / time_span
                    else:
                        frequency = 1  # 默认值
                else:
                    frequency = 1  # 默认值
                    
                market_data['sell_metrics'] = {
                    'avg_price': avg_sell_price,
                    'last_price': last_sell_price,
                    'avg_amount': avg_sell_amount,
                    'avg_frequency': frequency
                }
                
        # 计算平均价差
        orderbook = market_data['orderbook']
        if orderbook and orderbook['asks'] and orderbook['bids']:
            best_ask = orderbook['asks'][0][0]
            best_bid = orderbook['bids'][0][0]
            market_data['avg_spread'] = best_ask - best_bid
    
    def calculate_signals(self, symbol: str) -> Dict:
        """计算交易信号
        
        根据当前市场数据计算买入、卖出或平仓信号
        
        Args:
            symbol: 交易对符号
            
        Returns:
            Dict: 包含买入、卖出和平仓信号的字典
        """
        # 默认无信号
        signals = {
            'buy': False,
            'sell': False,
            'close': False,
            'trend': 'neutral'
        }
        
        # 获取当前市场数据
        market_data = self.market_data.get(symbol)
        if not market_data:
            return signals
            
        # 获取订单簿数据
        orderbook = market_data.get('orderbook')
        if not orderbook or not orderbook.get('bids') or not orderbook.get('asks'):
            return signals
            
        # 获取当前价格
        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])
        
        if not bids or not asks:
            return signals
            
        current_bid = float(bids[0][0])
        current_ask = float(asks[0][0])
        mid_price = (current_bid + current_ask) / 2
        
        # 获取持仓信息
        position = market_data.get('position')
        
        # 计算买卖压力 - 安全处理列表长度
        max_depth = min(5, len(bids), len(asks))
        if max_depth <= 0:
            return signals
            
        bid_volume = sum(float(bid[1]) for bid in bids[:max_depth])
        ask_volume = sum(float(ask[1]) for ask in asks[:max_depth])
        
        # 计算买卖压力比
        buy_sell_ratio = bid_volume / ask_volume if ask_volume > 0 else 1.0
        
        # 获取最近交易
        trades = market_data.get('trades', [])
        
        # 确保使用整数切片
        recent_trades_count = min(20, len(trades))
        recent_trades = trades[-recent_trades_count:] if recent_trades_count > 0 else []
        
        # 检查是否有足够的交易数据
        if len(recent_trades) < 5:  # 降低所需交易数据量
            # 数据不足，使用简单策略
            if buy_sell_ratio > 1.2:  # 降低阈值从1.5到1.2
                signals['buy'] = True
                signals['trend'] = 'bullish'
            elif buy_sell_ratio < 0.8:  # 提高阈值从0.7到0.8
                signals['sell'] = True
                signals['trend'] = 'bearish'
            return signals
        
        # 计算最近交易的价格变化趋势
        try:
            prices = [float(trade.get('price', 0)) for trade in recent_trades]
            if not prices or prices[0] == 0:
                return signals
                
            price_change = (prices[-1] - prices[0]) / prices[0]
            
            # 降低信号触发门槛
            if price_change > 0.0005 and buy_sell_ratio > 1.05:  # 原来是0.002和1.2
                signals['buy'] = True
                signals['trend'] = 'bullish'
            elif price_change < -0.0005 and buy_sell_ratio < 0.95:  # 原来是-0.002和0.8
                signals['sell'] = True
                signals['trend'] = 'bearish'
        except (TypeError, IndexError) as e:
            self.logger.error(f"Error calculating price change: {e}")
            return signals
        
        # 平仓逻辑
        if position:
            try:
                position_size = float(position.get('contracts', 0))
                unrealized_pnl = float(position.get('unrealizedPnl', 0))
                entry_price = float(position.get('entryPrice', 0))
                
                # 如果有多仓
                if position_size > 0:
                    # 止盈: 当价格上涨超过0.5%时 (降低止盈点)
                    if mid_price > entry_price * 1.005:
                        signals['close'] = True
                    # 止损: 当价格下跌超过0.3%时 (降低止损点)
                    elif mid_price < entry_price * 0.997:
                        signals['close'] = True
                    # 当信号是卖出且有多仓，平仓
                    elif signals['sell']:
                        signals['close'] = True
                        signals['sell'] = False
                
                # 如果有空仓
                elif position_size < 0:
                    # 止盈: 当价格下跌超过0.5%时 (降低止盈点)
                    if mid_price < entry_price * 0.995:
                        signals['close'] = True
                    # 止损: 当价格上涨超过0.3%时 (降低止损点)
                    elif mid_price > entry_price * 1.003:
                        signals['close'] = True
                    # 当信号是买入且有空仓，平仓
                    elif signals['buy']:
                        signals['close'] = True
                        signals['buy'] = False
            except (TypeError, ValueError) as e:
                self.logger.error(f"Error processing position data: {e}")
        
        return signals
    
    def calculate_order_prices(self, symbol: str, trend: str) -> Dict:
        """计算订单价格
        
        根据当前市场数据和趋势计算买入和卖出价格
        
        Args:
            symbol: 交易对符号
            trend: 市场趋势 ('bullish', 'bearish', 'neutral')
            
        Returns:
            Dict: 包含买入和卖出价格的字典
        """
        # 获取当前市场数据
        market_data = self.market_data.get(symbol)
        if not market_data:
            return {'buy_price': 0, 'sell_price': 0}
            
        # 获取订单簿数据
        orderbook = market_data.get('orderbook')
        if not orderbook or not orderbook.get('bids') or not orderbook.get('asks'):
            return {'buy_price': 0, 'sell_price': 0}
            
        # 获取当前价格
        current_bid = float(orderbook['bids'][0][0])
        current_ask = float(orderbook['asks'][0][0])
        
        # 根据趋势设置价格
        if trend == 'bullish':
            # 看涨趋势，买入价略高于最高买单，卖出价高于当前卖价
            buy_price = current_bid * 1.0003
            sell_price = current_ask * 1.002
        elif trend == 'bearish':
            # 看跌趋势，买入价低于当前买价，卖出价略低于最低卖单
            buy_price = current_bid * 0.998
            sell_price = current_ask * 0.9997
        else:
            # 中性趋势，使用当前价格
            buy_price = current_bid
            sell_price = current_ask
        
        # 确保价格在有效范围内
        market_info = self.exchange.markets.get(symbol, {})
        price_precision = market_info.get('precision', {}).get('price', 8)
        
        # 确保精度是整数
        if isinstance(price_precision, float):
            price_precision = int(price_precision)
        
        # 四舍五入到指定精度
        buy_price = round(buy_price, price_precision)
        sell_price = round(sell_price, price_precision)
        
        return {'buy_price': buy_price, 'sell_price': sell_price}
    
    def calculate_order_amounts(self, symbol: str, trend: str) -> Dict:
        """计算订单数量
        
        根据当前市场数据和趋势计算买入和卖出数量
        
        Args:
            symbol: 交易对符号
            trend: 市场趋势 ('bullish', 'bearish', 'neutral')
            
        Returns:
            Dict: 包含买入和卖出数量的字典
        """
        # 默认的基础下单量
        base_amount = self.trading_config.get('position_size', 0.01)
        
        # 根据趋势调整下单量
        if trend == 'bullish':
            buy_amount = base_amount
            sell_amount = base_amount * 0.5  # 看涨趋势卖出量减半
        elif trend == 'bearish':
            buy_amount = base_amount * 0.5  # 看跌趋势买入量减半
            sell_amount = base_amount
        else:
            buy_amount = base_amount
            sell_amount = base_amount
        
        # 获取市场信息，确保数量符合交易所要求
        market_info = self.exchange.markets.get(symbol, {})
        amount_precision = market_info.get('precision', {}).get('amount', 8)
        
        # 确保精度是整数
        if isinstance(amount_precision, float):
            amount_precision = int(amount_precision)
        
        # 四舍五入到指定精度
        buy_amount = round(buy_amount, amount_precision)
        sell_amount = round(sell_amount, amount_precision)
        
        return {'buy_amount': buy_amount, 'sell_amount': sell_amount}
    
    async def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Optional[Dict]:
        """下限价单"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 检查余额
                balance = await self.exchange.fetch_balance()
                if side == 'buy':
                    currency = symbol.split('/')[1]  # 获取交易对的计价货币 (如USDT)
                    available = float(balance['free'][currency]) if currency in balance['free'] else 0
                    required = amount * price * 1.01  # 加1%的滑点
                    
                    if available < required:
                        self.logger.warning(f"Insufficient balance for {side} order: {available} < {required}")
                        return None
                
                # 创建订单
                order = await self.exchange.create_limit_order(
                    symbol=symbol,
                    side=side,
                    amount=amount,
                    price=price
                )
                
                # 保存到待处理订单
                self.pending_orders[order['id']] = {
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'timestamp': time.time()
                }
                
                # 更新性能指标
                if hasattr(self, 'performance_monitor'):
                    self.performance_monitor.update_order_metrics('success')
                
                return order
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if "502 Bad Gateway" in error_msg and retry_count < max_retries:
                    self.logger.warning(f"Received 502 Bad Gateway when placing {side} limit order for {symbol}, retry {retry_count}/{max_retries}")
                    await asyncio.sleep(retry_count)  # 增加退避时间
                else:
                    # 记录错误
                    self.logger.error(f"Failed to place {side} limit order for {symbol}: {error_msg}")
                    
                    # 更新性能指标
                    if hasattr(self, 'performance_monitor'):
                        self.performance_monitor.update_order_metrics('failed')
                    
                    # 处理特定错误
                    if 'insufficient balance' in str(e).lower():
                        self.logger.warning(f"Insufficient balance for {side} order")
                    elif 'min notional' in str(e).lower():
                        self.logger.warning(f"Order amount too small for {symbol}")
                    
                    if retry_count >= max_retries or "502 Bad Gateway" not in error_msg:
                        return None  # 最大重试次数后或非502错误，返回None
        
        return None

    async def place_market_order(self, symbol: str, side: str, amount: float) -> Optional[Dict]:
        """下市价单"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 检查余额
                balance = await self.exchange.fetch_balance()
                if side == 'buy':
                    currency = symbol.split('/')[1]  # 获取交易对的计价货币 (如USDT)
                    available = float(balance['free'][currency]) if currency in balance['free'] else 0
                    
                    # 获取当前市场价格
                    ticker = await self.exchange.fetch_ticker(symbol)
                    estimated_price = ticker['last']
                    required = amount * estimated_price * 1.02  # 加2%的滑点
                    
                    if available < required:
                        self.logger.warning(f"Insufficient balance for {side} market order: {available} < {required}")
                        return None
                
                # 创建市价单
                order = await self.exchange.create_market_order(
                    symbol=symbol,
                    side=side,
                    amount=amount
                )
                
                # 记录订单信息
                self.logger.info(f"Placed {side} market order for {symbol}: {amount}")
                
                # 更新性能指标
                if hasattr(self, 'performance_monitor'):
                    self.performance_monitor.update_order_metrics('success')
                
                return order
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if "502 Bad Gateway" in error_msg and retry_count < max_retries:
                    self.logger.warning(f"Received 502 Bad Gateway when placing {side} market order for {symbol}, retry {retry_count}/{max_retries}")
                    await asyncio.sleep(retry_count)  # 增加退避时间
                else:
                    # 记录错误
                    self.logger.error(f"Failed to place {side} market order for {symbol}: {error_msg}")
                    
                    # 更新性能指标
                    if hasattr(self, 'performance_monitor'):
                        self.performance_monitor.update_order_metrics('failed')
                    
                    # 处理特定错误
                    if 'insufficient balance' in str(e).lower():
                        self.logger.warning(f"Insufficient balance for {side} market order")
                    elif 'min notional' in str(e).lower():
                        self.logger.warning(f"Order amount too small for {symbol}")
                    
                    if retry_count >= max_retries or "502 Bad Gateway" not in error_msg:
                        return None  # 最大重试次数后或非502错误，返回None
        
        return None
    
    async def handle_pending_orders(self):
        """处理未完成的订单"""
        current_time = time.time()
        orders_to_remove = []
        
        # 创建待处理订单的副本进行迭代，避免"dictionary changed size during iteration"错误
        pending_orders_copy = dict(self.pending_orders)
        
        for order_id, order_info in pending_orders_copy.items():
            # 更新订单信息，记录API错误次数
            if 'api_error_count' not in order_info:
                order_info['api_error_count'] = 0
            if 'last_error_time' not in order_info:
                order_info['last_error_time'] = 0
            
            # 检查是否超时
            time_diff = current_time - order_info['timestamp']
            if time_diff > self.strategy_config.get('order_timeout', 15):  # 默认15秒超时
                self.logger.warning(f"Order {order_id} timeout, canceling...")
                # 尝试取消订单
                if await self.cancel_order(order_id, order_info['symbol']):
                    orders_to_remove.append(order_id)
                
            else:
                # 检查订单状态
                try:
                    # 添加重试逻辑
                    max_retries = 3
                    retry_count = 0
                    order_status = None
                    
                    while retry_count < max_retries:
                        try:
                            order_status = await self.exchange.fetch_order(order_id, order_info['symbol'])
                            # 成功获取订单状态，重置错误计数
                            order_info['api_error_count'] = 0
                            break  # 成功获取订单状态，跳出循环
                        except Exception as retry_error:
                            retry_count += 1
                            if "502 Bad Gateway" in str(retry_error):
                                self.logger.warning(f"Received 502 Bad Gateway when checking order {order_id}, retry {retry_count}/{max_retries}")
                                if retry_count < max_retries:
                                    await asyncio.sleep(1)  # 等待1秒后重试
                                else:
                                    # 最后一次重试也失败，记录错误并继续
                                    order_info['api_error_count'] += 1
                                    order_info['last_error_time'] = current_time
                                    
                                    self.logger.error(f"Failed to check order {order_id} status after {max_retries} retries: {str(retry_error)}")
                                    
                                    # 连续API错误超过阈值，自动取消订单
                                    if order_info['api_error_count'] >= 3:
                                        self.logger.warning(f"Order {order_id} has experienced {order_info['api_error_count']} consecutive API failures, auto-canceling")
                                        await self.cancel_order(order_id, order_info['symbol'])
                                        orders_to_remove.append(order_id)
                                    # 如果订单已经存在超过2分钟，认为可能有问题，尝试取消
                                    elif time_diff > 120:
                                        self.logger.warning(f"Order {order_id} has been pending for >2min with API issues, canceling...")
                                        await self.cancel_order(order_id, order_info['symbol'])
                                        orders_to_remove.append(order_id)
                            else:
                                # 其他错误直接抛出
                                raise retry_error
                    
                    # 处理订单状态
                    if order_status:
                        if order_status['status'] == 'closed' or order_status['status'] == 'filled':
                            # 订单已成交
                            self.logger.info(f"Order {order_id} filled: {order_status['filled']} @ {order_status['price']}")
                            orders_to_remove.append(order_id)
                            
                            # 记录成交数据
                            if self.data_storage:
                                await self.data_storage.save_order({
                                    'id': order_id,
                                    'symbol': order_info['symbol'],
                                    'side': order_info['side'],
                                    'price': float(order_status['price']),
                                    'amount': float(order_status['filled']),
                                    'timestamp': dt.now().timestamp(),
                                    'status': order_status['status']
                                })
                        
                        elif order_status['status'] == 'canceled':
                            # 订单已取消
                            self.logger.info(f"Order {order_id} canceled")
                            orders_to_remove.append(order_id)
                
                except Exception as e:
                    # 记录API错误但保留订单
                    order_info['api_error_count'] += 1
                    order_info['last_error_time'] = current_time
                    
                    # 如果连续错误超过阈值且时间间隔较短，取消订单
                    if order_info['api_error_count'] >= 5:
                        self.logger.warning(f"Order {order_id} has experienced {order_info['api_error_count']} API failures, auto-canceling")
                        await self.cancel_order(order_id, order_info['symbol'])
                        orders_to_remove.append(order_id)
                    
                    self.logger.error(f"Failed to check order {order_id} status: {str(e)}")
        
        # 移除已处理的订单
        for order_id in orders_to_remove:
            if order_id in self.pending_orders:
                del self.pending_orders[order_id]
    
    async def process_symbol(self, symbol: str):
        """处理单个交易对"""
        try:
            # 更新市场数据
            await self.update_market_data(symbol)
            
            # 检查是否有有效的市场数据
            market_data = self.market_data.get(symbol, {})
            current_time = time.time()
            last_update = market_data.get('last_update', 0)
            
            # 如果数据超过2分钟未更新，跳过此次处理
            if current_time - last_update > 120:
                self.logger.warning(f"Skipping processing for {symbol} due to stale market data")
                return
            
            # 首先检查风险限制
            try:
                # 获取当前持仓和未成交订单
                total_balance = 0
                total_position_size = 0
                open_orders_count = 0
                
                # 计算当前总持仓大小
                for sym, data in self.market_data.items():
                    if data.get('position'):
                        position_size = abs(float(data['position'].get('contracts', 0)))
                        total_position_size += position_size
                
                # 获取未成交订单数量
                open_orders_count = len(self.pending_orders)
                
                # 获取账户余额
                max_retries = 3
                retry_count = 0
                account = None
                
                while retry_count < max_retries and account is None:
                    try:
                        account = await self.exchange.fetch_balance()
                    except Exception as balance_error:
                        retry_count += 1
                        if "502 Bad Gateway" in str(balance_error) and retry_count < max_retries:
                            self.logger.warning(f"Received 502 Bad Gateway when fetching balance, retry {retry_count}/{max_retries}")
                            await asyncio.sleep(retry_count)  # 增加退避时间
                        else:
                            self.logger.error(f"Failed to fetch balance: {str(balance_error)}")
                            return  # 如果无法获取余额，跳过此次处理
                
                if account:
                    if 'USDT' in account['total']:
                        total_balance = float(account['total']['USDT'])
                    elif 'BUSD' in account['total']:
                        total_balance = float(account['total']['BUSD'])
                
                if not self.risk_manager.check_risk_limits(total_balance, total_position_size, open_orders_count):
                    self.logger.warning(f"Risk limits reached for {symbol}, skipping")
                    return
            except Exception as e:
                self.logger.error(f"Failed to check risk limits: {str(e)}")
                self.logger.warning(f"Risk limits reached for {symbol}, skipping")
                return
            
            # 计算信号
            signal = self.calculate_signals(symbol)
            
            # 获取当前订单簿和价格
            orderbook = self.market_data[symbol].get('orderbook')
            if not orderbook or not orderbook.get('bids') or not orderbook.get('asks'):
                return
                
            current_bid = float(orderbook['bids'][0][0])
            current_ask = float(orderbook['asks'][0][0])
            
            # 根据信号计算价格和数量
            prices = self.calculate_order_prices(symbol, signal['trend'])
            amounts = self.calculate_order_amounts(symbol, signal['trend'])
            
            # 获取当前持仓
            position = self.market_data[symbol].get('position')
            has_position = position and abs(float(position.get('contracts', 0))) > 0
            
            # 执行交易
            if signal['close']:
                # 平仓逻辑
                if position:
                    if float(position.get('contracts', 0)) > 0:
                        # 平多仓
                        self.logger.info(f"Closing long position for {symbol}")
                        await self.place_market_order(symbol, 'sell', abs(float(position.get('contracts', 0))))
                    elif float(position.get('contracts', 0)) < 0:
                        # 平空仓
                        self.logger.info(f"Closing short position for {symbol}")
                        await self.place_market_order(symbol, 'buy', abs(float(position.get('contracts', 0))))
            elif signal['buy']:
                # 买入信号
                if amounts['buy_amount'] > 0 and prices['buy_price'] > 0:
                    self.logger.info(f"Placing buy order for {symbol}: {amounts['buy_amount']} @ {prices['buy_price']}")
                    await self.place_limit_order(symbol, 'buy', amounts['buy_amount'], prices['buy_price'])
            elif signal['sell']:
                # 卖出信号
                if amounts['sell_amount'] > 0 and prices['sell_price'] > 0:
                    self.logger.info(f"Placing sell order for {symbol}: {amounts['sell_amount']} @ {prices['sell_price']}")
                    await self.place_limit_order(symbol, 'sell', amounts['sell_amount'], prices['sell_price'])
            else:
                # 无明确信号，但如果没有持仓且没有未成交订单，尝试加入市场
                if not has_position and open_orders_count < 2 and abs(total_position_size) < self.trading_config.get('max_position_size', 0.15):
                    # 随机选择方向，偏向于市场趋势
                    if random.random() > 0.5:  # 50%概率做多
                        amount = self.trading_config.get('position_size', 0.03) * 0.5  # 使用较小数量
                        price = current_bid * 0.9998  # 略低于当前买价
                        self.logger.info(f"[主动下单] 买入 {symbol}: {amount} @ {price}")
                        await self.place_limit_order(symbol, 'buy', amount, price)
                    else:  # 50%概率做空
                        amount = self.trading_config.get('position_size', 0.03) * 0.5  # 使用较小数量
                        price = current_ask * 1.0002  # 略高于当前卖价
                        self.logger.info(f"[主动下单] 卖出 {symbol}: {amount} @ {price}")
                        await self.place_limit_order(symbol, 'sell', amount, price)
                
        except Exception as e:
            self.logger.error(f"Error processing symbol {symbol}: {str(e)}")
    
    async def run_async(self):
        """异步运行策略"""
        await self.initialize()
        
        # 监控更新间隔
        update_interval = min(5, self.strategy_config.get('order_update_interval', 5))
        
        # 添加错误恢复计数器
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        try:
            while True:
                try:
                    cycle_start = time.time()
                    
                    # 检查待处理订单
                    await self.handle_pending_orders()
                    
                    # 处理每个交易对
                    symbols = self.trading_config['symbols']
                    for symbol in symbols:
                        await self.process_symbol(symbol)
                    
                    # 检查风险限制
                    balance = await self.exchange.fetch_balance()
                    if not self.risk_manager.can_trade(float(balance['total']['USDT'])):
                        self.logger.warning("Risk limits reached, stopping trading")
                        break
                    
                    # 记录延迟
                    cycle_latency = time.time() - cycle_start
                    self.latency_metrics['cycle_latency'].append(cycle_latency)
                    
                    # 重置错误计数器，因为成功执行了一个完整循环
                    consecutive_errors = 0
                    
                    # 等待下一个周期
                    sleep_time = max(0, update_interval - cycle_latency)
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                    
                except RuntimeError as e:
                    # 处理"dictionary changed size during iteration"等运行时错误
                    if "dictionary changed size during iteration" in str(e):
                        self.logger.error(f"捕获到字典迭代错误: {str(e)}")
                        consecutive_errors += 1
                        self.logger.warning(f"正在恢复... 错误计数: {consecutive_errors}/{max_consecutive_errors}")
                        
                        # 休眠一段时间以避免相同错误立即再次发生
                        await asyncio.sleep(1)
                        
                        # 如果连续错误太多，还是应该中断
                        if consecutive_errors >= max_consecutive_errors:
                            self.logger.critical(f"连续错误过多 ({consecutive_errors}), 停止策略")
                            raise e
                    else:
                        # 其他运行时错误直接抛出
                        raise e
                        
                except Exception as e:
                    # 处理其他错误
                    self.logger.error(f"循环中捕获到错误: {str(e)}")
                    consecutive_errors += 1
                    self.logger.warning(f"正在恢复... 错误计数: {consecutive_errors}/{max_consecutive_errors}")
                    
                    # 休眠一段时间以避免相同错误立即再次发生
                    await asyncio.sleep(2)
                    
                    # 如果连续错误太多，则中断
                    if consecutive_errors >= max_consecutive_errors:
                        self.logger.critical(f"连续错误过多 ({consecutive_errors}), 停止策略")
                        raise e
                
        except Exception as e:
            self.logger.error(f"Error in strategy run loop: {str(e)}")
        finally:
            # 收尾工作
            await self.data_storage.close()
            await self.exchange.close()
    
    def run(self):
        """同步运行入口"""
        asyncio.run(self.run_async())

    async def cancel_order(self, order_id: str, symbol: str):
        """取消订单"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # 如果订单在挂单列表中才尝试取消
                if order_id in self.pending_orders:
                    await self.exchange.cancel_order(order_id, symbol)
                    # 不在这里立即删除订单，而是返回True让调用者处理
                    self.logger.info(f"Order {order_id} successfully canceled")
                    return True
                else:
                    # 订单不在挂单列表中，可能已经成交或者已经被取消
                    self.logger.info(f"Order {order_id} not found in pending orders, may be filled or already cancelled")
                    return True
                    
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                if "Unknown order sent" in error_msg or "-2011" in error_msg:
                    # 订单不存在，可能已经成交或已被取消
                    self.logger.info(f"Order {order_id} already filled or canceled")
                    # 不在这里立即删除订单，而是返回True让调用者处理
                    return True
                    
                elif "502 Bad Gateway" in error_msg and retry_count < max_retries:
                    self.logger.warning(f"Received 502 Bad Gateway when canceling order {order_id}, retry {retry_count}/{max_retries}")
                    await asyncio.sleep(retry_count)  # 增加退避时间
                else:
                    self.logger.error(f"Failed to cancel order {order_id}: {error_msg}")
                    
                    # 如果是最后一次重试且是API连接问题，从挂单列表中移除以避免卡住
                    if retry_count >= max_retries and "502 Bad Gateway" in error_msg:
                        self.logger.warning(f"Removing order {order_id} from pending list after multiple failed cancellation attempts")
                        # 不在这里立即删除订单，而是返回True让调用者处理
                        return True
                    
                    if retry_count >= max_retries:
                        return False
        
        return False 