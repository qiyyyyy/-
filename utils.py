"""
Utility functions for trading bot
"""
import logging
import time
import asyncio
from datetime import datetime
import json
import os
import statistics
from typing import Dict, List, Any, Optional, Tuple, Callable
import numpy as np
from decimal import Decimal, ROUND_DOWN

# 全局异步工具函数
async def handle_api_error(error: Exception, exchange_name: str, 
                         action: str, retry_function: Optional[Callable] = None, 
                         retry_args: tuple = (), retry_kwargs: Dict = None,
                         max_retries: int = 3, backoff_factor: float = 2.0) -> Optional[Any]:
    """
    处理API错误，特别针对交易所API的常见错误
    
    Args:
        error: 捕获的异常
        exchange_name: 交易所名称
        action: 正在执行的操作描述
        retry_function: 可选的重试函数
        retry_args: 重试函数的位置参数
        retry_kwargs: 重试函数的关键字参数
        max_retries: 最大重试次数
        backoff_factor: 退避因子
    
    Returns:
        重试成功时返回结果，否则返回None
    """
    error_msg = str(error)
    logger = logging.getLogger('API')
    
    # 检测Windows aiodns错误并尝试修复
    if 'aiodns needs a SelectorEventLoop on Windows' in error_msg:
        logger.info(f"Windows aiodns错误 ({action}): {error_msg}")
        try:
            import platform
            if platform.system() == 'Windows':
                import asyncio
                import selectors
                selector = selectors.SelectSelector()
                loop = asyncio.SelectorEventLoop(selector)
                asyncio.set_event_loop(loop)
                logger.info("已设置Windows SelectorEventLoop")
                
                # 如果提供了重试函数，尝试重试
                if retry_function:
                    try:
                        if retry_args:
                            await retry_function(*retry_args)
                        else:
                            await retry_function()
                        return True
                    except Exception as retry_error:
                        logger.warning(f"重试失败 (1/3): {str(retry_error)}")
                        # 再次尝试
                        try:
                            await asyncio.sleep(1)
                            if retry_args:
                                await retry_function(*retry_args)
                            else:
                                await retry_function()
                            return True
                        except Exception as retry_error2:
                            logger.warning(f"重试失败 (2/3): {str(retry_error2)}")
                            # 最后一次尝试
                            try:
                                await asyncio.sleep(2)
                                if retry_args:
                                    await retry_function(*retry_args)
                                else:
                                    await retry_function()
                                return True
                            except Exception as retry_error3:
                                logger.warning(f"重试失败 (3/3): {str(retry_error3)}")
        except Exception as e:
            logger.error(f"无法修复Windows事件循环: {str(e)}")
    
    # 记录详细错误信息
    logger.error(f"{exchange_name} API错误 ({action}): {error_msg}")
    
    # 常见API错误处理
    if "Invalid Api-Key ID" in error_msg or "-2015" in error_msg:
        logger.critical(f"{exchange_name} API密钥无效 ({action})")
        if 'testnet' in error_msg.lower() or 'test' in error_msg.lower():
            logger.critical(f"可能使用了主网API密钥连接测试网，请检查配置")
        return False
        
    elif "Invalid signature" in error_msg or "-2014" in error_msg:
        logger.critical(f"{exchange_name} API签名无效 ({action})")
        logger.critical("请检查API密钥和密钥是否匹配，以及服务器时间是否同步")
        return False
        
    elif "IP has been banned" in error_msg or "-2015" in error_msg:
        logger.error(f"{exchange_name} IP已被禁止 ({action})")
        logger.error("您的IP地址已被交易所临时限制，请等待一段时间再尝试")
        return False
        
    elif "Too many requests" in error_msg or "429" in error_msg or "-1003" in error_msg:
        logger.error(f"{exchange_name} 请求频率过高 ({action})")
        logger.error("请降低请求频率或等待一段时间再继续")
        
        # 如果提供了重试函数，等待后尝试重试
        if retry_function:
            try:
                await asyncio.sleep(5)  # 等待5秒
                if retry_args:
                    await retry_function(*retry_args)
                else:
                    await retry_function()
                return True
            except Exception as retry_error:
                logger.warning(f"重试失败: {str(retry_error)}")
        return False
        
    elif "502 Bad Gateway" in error_msg:
        logger.error(f"{exchange_name} 服务器暂时不可用 ({action})")
        logger.error("交易所API服务器可能过载，请稍后再试")
        
        # 如果提供了重试函数，等待后尝试重试
        if retry_function:
            try:
                await asyncio.sleep(2)  # 等待2秒
                if retry_args:
                    await retry_function(*retry_args)
                else:
                    await retry_function()
                return True
            except Exception as retry_error:
                logger.warning(f"重试失败: {str(retry_error)}")
        return False
    
    # 重试逻辑
    if retry_function and max_retries > 0:
        retry_kwargs = retry_kwargs or {}
        
        for attempt in range(max_retries):
            try:
                delay = backoff_factor ** attempt
                logger.info(f"尝试重试 {action}，{delay:.2f}秒后第{attempt+1}次尝试")
                await asyncio.sleep(delay)
                result = await retry_function(*retry_args, **retry_kwargs)
                logger.info(f"重试成功: {action}")
                return result
            except Exception as retry_error:
                logger.warning(f"重试失败 ({attempt+1}/{max_retries}): {str(retry_error)}")
                
    return None

class Logger:
    def __init__(self, name: str, log_file: str = None, log_level: str = 'INFO'):
        self.logger = logging.getLogger(name)
        
        # 设置日志级别
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
        
        # 内存日志缓冲，用于高频场景避免IO瓶颈
        self.log_buffer = []
        self.last_flush_time = time.time()
        self.flush_interval = 5  # 5秒刷新一次到文件
    
    def info(self, message: str):
        self.logger.info(message)
        self._buffer_log('INFO', message)
    
    def error(self, message: str):
        self.logger.error(message)
        self._buffer_log('ERROR', message)
    
    def warning(self, message: str):
        self.logger.warning(message)
        self._buffer_log('WARNING', message)
    
    def debug(self, message: str):
        self.logger.debug(message)
        self._buffer_log('DEBUG', message)
    
    def _buffer_log(self, level: str, message: str):
        """缓存日志，减少IO操作"""
        self.log_buffer.append({
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        })
        
        # 检查是否需要刷新缓冲
        if time.time() - self.last_flush_time > self.flush_interval or len(self.log_buffer) > 100:
            self.flush_buffer()
    
    def flush_buffer(self):
        """将缓冲的日志写入文件"""
        if not self.log_buffer:
            return
            
        try:
            # 将缓冲区的日志批量写入文件
            log_dir = 'data/logs'
            os.makedirs(log_dir, exist_ok=True)
            
            filename = f"log_{datetime.now().strftime('%Y%m%d')}.json"
            filepath = os.path.join(log_dir, filename)
            
            with open(filepath, 'a') as f:
                for log in self.log_buffer:
                    f.write(json.dumps(log) + '\n')
            
            # 清空缓冲区
            self.log_buffer = []
            self.last_flush_time = time.time()
        except Exception as e:
            # 如果写入失败，记录到控制台但不影响程序运行
            print(f"Failed to write log buffer: {str(e)}")

class DataProcessor:
    @staticmethod
    def calculate_volume_metrics(trades: List[Dict], window: int) -> Dict:
        """计算成交量指标"""
        current_time = time.time() * 1000  # 转换为毫秒
        recent_trades = [t for t in trades if current_time - t['timestamp'] <= window * 1000]
        
        if not recent_trades:
            return {'avg_volume': 0, 'volume_std': 0, 'trade_count': 0, 'volume_per_second': 0}
        
        volumes = [float(t['amount']) for t in recent_trades]
        
        # 计算每秒成交量
        time_span = (recent_trades[-1]['timestamp'] - recent_trades[0]['timestamp']) / 1000  # 毫秒转秒
        volume_per_second = sum(volumes) / (time_span if time_span > 0 else 1)
        
        return {
            'avg_volume': np.mean(volumes),
            'volume_std': np.std(volumes),
            'trade_count': len(recent_trades),
            'volume_per_second': volume_per_second
        }
    
    @staticmethod
    def calculate_price_metrics(trades: List[Dict], window: int) -> Dict:
        """计算价格指标"""
        current_time = time.time() * 1000  # 转换为毫秒
        recent_trades = [t for t in trades if current_time - t['timestamp'] <= window * 1000]
        
        if not recent_trades or len(recent_trades) < 2:
            return {'avg_price': 0, 'price_std': 0, 'price_change': 0, 'price_momentum': 0}
        
        prices = [float(t['price']) for t in recent_trades]
        
        # 计算动量 (短期价格变化率)
        if len(prices) >= 5:
            short_term = prices[-5:]
            momentum = (short_term[-1] - short_term[0]) / short_term[0] if short_term[0] != 0 else 0
        else:
            momentum = 0
            
        return {
            'avg_price': np.mean(prices),
            'price_std': np.std(prices),
            'price_change': (prices[-1] - prices[0]) / prices[0] if prices[0] != 0 else 0,
            'price_momentum': momentum
        }
    
    @staticmethod
    def calculate_spread(orderbook: Dict) -> Dict:
        """计算买卖价差及深度指标"""
        if not orderbook or not orderbook.get('bids') or not orderbook.get('asks'):
            return {'spread': float('inf'), 'bid_ask_ratio': 0, 'depth_imbalance': 0}
        
        spread = float(orderbook['asks'][0][0]) - float(orderbook['bids'][0][0])
        
        # 计算买卖深度比率 (前5档)
        bid_depth = sum([float(b[1]) for b in orderbook['bids'][:5]])
        ask_depth = sum([float(a[1]) for a in orderbook['asks'][:5]])
        
        bid_ask_ratio = bid_depth / ask_depth if ask_depth > 0 else 0
        
        # 深度不平衡指标 (买卖差异占总深度的比例)
        total_depth = bid_depth + ask_depth
        depth_imbalance = (bid_depth - ask_depth) / total_depth if total_depth > 0 else 0
        
        return {
            'spread': spread,
            'bid_ask_ratio': bid_ask_ratio,
            'depth_imbalance': depth_imbalance
        }
    
    @staticmethod
    def analyze_trade_flow(buy_trades: List[Dict], sell_trades: List[Dict], window: int = 10) -> Dict:
        """分析买卖交易流向"""
        current_time = time.time() * 1000
        recent_buys = [t for t in buy_trades if current_time - t['timestamp'] <= window * 1000]
        recent_sells = [t for t in sell_trades if current_time - t['timestamp'] <= window * 1000]
        
        if not recent_buys and not recent_sells:
            return {
                'buy_volume': 0,
                'sell_volume': 0,
                'buy_count': 0,
                'sell_count': 0,
                'flow_ratio': 1.0,  # 默认平衡
                'avg_buy_size': 0,
                'avg_sell_size': 0
            }
        
        # 计算交易量和次数
        buy_volume = sum([float(t['amount']) for t in recent_buys])
        sell_volume = sum([float(t['amount']) for t in recent_sells])
        
        # 计算平均交易大小
        avg_buy_size = buy_volume / len(recent_buys) if recent_buys else 0
        avg_sell_size = sell_volume / len(recent_sells) if recent_sells else 0
        
        # 计算流量比率 (买/卖)
        flow_ratio = buy_volume / sell_volume if sell_volume > 0 else (float('inf') if buy_volume > 0 else 1.0)
        
        return {
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'buy_count': len(recent_buys),
            'sell_count': len(recent_sells),
            'flow_ratio': flow_ratio,
            'avg_buy_size': avg_buy_size,
            'avg_sell_size': avg_sell_size
        }

class RiskManager:
    """风险管理器"""
    def __init__(self, trading_config: Dict):
        self.trading_config = trading_config
        self.max_drawdown = trading_config.get('max_drawdown', 0.15)  # 放宽最大回撤比例
        self.max_position_size = trading_config.get('max_positions', 5) * trading_config.get('position_size', 0.03)
        self.max_open_orders = trading_config.get('max_open_orders', 10)
        self.initial_balance = 0
        self.lowest_balance = float('inf')
        
        # 创建日志记录器
        import os
        import datetime
        
        # 使用相同的日志目录
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # 创建带时间戳的日志文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(logs_dir, f'risk_manager_{timestamp}.log')
        
        self.logger = Logger('RiskManager', log_file=log_file)
    
    def set_initial_balance(self, balance: float):
        """设置初始余额"""
        self.initial_balance = balance
        self.lowest_balance = balance
    
    def can_trade(self, current_balance: float) -> bool:
        """检查是否可以继续交易"""
        # 更新最低余额
        if current_balance < self.lowest_balance:
            self.lowest_balance = current_balance
        
        # 如果初始余额尚未设置，设置它
        if self.initial_balance == 0:
            self.set_initial_balance(current_balance)
            return True
        
        # 计算回撤
        drawdown = 1 - (current_balance / self.initial_balance)
        
        # 检查回撤是否超过限制
        if drawdown > self.max_drawdown:
            self.logger.warning(f"Maximum drawdown reached: {drawdown:.2%}")
            return False
        
        return True
    
    def check_risk_limits(self, total_balance: float, total_position_size: float, open_orders_count: int) -> bool:
        """检查风险限制
        
        Args:
            total_balance (float): 总账户余额
            total_position_size (float): 总持仓大小
            open_orders_count (int): 未成交订单数量
            
        Returns:
            bool: 是否符合风险限制
        """
        # 更新最低余额
        if total_balance < self.lowest_balance:
            self.lowest_balance = total_balance
        
        # 如果初始余额尚未设置，设置它
        if self.initial_balance == 0:
            self.set_initial_balance(total_balance)
            return True
        
        # 计算回撤
        drawdown = 1 - (total_balance / self.initial_balance)
        
        # 检查风险条件
        if drawdown > self.max_drawdown:
            self.logger.warning(f"最大回撤超过限制: {drawdown:.2%} > {self.max_drawdown:.2%}")
            return False
            
        if total_position_size > self.max_position_size:
            self.logger.warning(f"最大持仓超过限制: {total_position_size} > {self.max_position_size}")
            return False
            
        if open_orders_count > self.max_open_orders:
            self.logger.warning(f"未成交订单数量超过限制: {open_orders_count} > {self.max_open_orders}")
            return False
            
        return True

class DataStorage:
    """数据存储类"""
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        self.trades_dir = os.path.join(data_dir, 'trades')
        self.balances_dir = os.path.join(data_dir, 'balances')
        self.orders_dir = os.path.join(data_dir, 'orders')
        self.metrics_dir = os.path.join(data_dir, 'metrics')
        
        # 确保目录存在
        for directory in [self.trades_dir, self.balances_dir, self.orders_dir, self.metrics_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # 交易缓冲区
        self.trades_buffer = []
        self.balances_buffer = []
        self.max_buffer_size = 50
    
    async def save_trade(self, trade_data: Dict) -> None:
        """保存交易记录"""
        date_str = datetime.now().strftime('%Y%m%d')
        filename = os.path.join(self.trades_dir, f'trades_{date_str}.json')
        
        # 添加到缓冲区
        self.trades_buffer.append(trade_data)
        
        # 缓冲区满时写入文件
        if len(self.trades_buffer) >= self.max_buffer_size:
            await self._flush_trades_buffer()
    
    async def _flush_trades_buffer(self) -> None:
        """将交易缓冲区写入文件"""
        if not self.trades_buffer:
            return
            
        date_str = datetime.now().strftime('%Y%m%d')
        filename = os.path.join(self.trades_dir, f'trades_{date_str}.json')
        
        try:
            # 读取现有文件
            trades = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    trades = json.load(f)
            
            # 添加新交易
            trades.extend(self.trades_buffer)
            
            # 写入文件
            with open(filename, 'w') as f:
                json.dump(trades, f, indent=2)
            
            # 清空缓冲区
            self.trades_buffer = []
        except Exception as e:
            print(f"Error flushing trades buffer: {str(e)}")
    
    async def save_balance(self, balance_data: Dict) -> None:
        """保存余额记录"""
        date_str = datetime.now().strftime('%Y%m%d')
        filename = os.path.join(self.balances_dir, f'balances_{date_str}.json')
        
        # 添加到缓冲区
        self.balances_buffer.append(balance_data)
        
        # 缓冲区满时写入文件
        if len(self.balances_buffer) >= self.max_buffer_size:
            await self._flush_balances_buffer()
    
    async def _flush_balances_buffer(self) -> None:
        """将余额缓冲区写入文件"""
        if not self.balances_buffer:
            return
            
        date_str = datetime.now().strftime('%Y%m%d')
        filename = os.path.join(self.balances_dir, f'balances_{date_str}.json')
        
        try:
            # 读取现有文件
            balances = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    balances = json.load(f)
            
            # 添加新余额记录
            balances.extend(self.balances_buffer)
            
            # 写入文件
            with open(filename, 'w') as f:
                json.dump(balances, f, indent=2)
            
            # 清空缓冲区
            self.balances_buffer = []
        except Exception as e:
            print(f"Error flushing balances buffer: {str(e)}")
    
    async def save_order(self, order_data: Dict) -> None:
        """保存订单记录"""
        date_str = datetime.now().strftime('%Y%m%d')
        filename = os.path.join(self.orders_dir, f'orders_{date_str}.json')
        
        try:
            # 读取现有文件
            orders = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    orders = json.load(f)
            
            # 添加新订单
            orders.append(order_data)
            
            # 写入文件
            with open(filename, 'w') as f:
                json.dump(orders, f, indent=2)
        except Exception as e:
            print(f"Error saving order: {str(e)}")
    
    async def save_metrics(self, metrics_data: Dict) -> None:
        """保存性能指标"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.metrics_dir, f'metrics_{timestamp}.json')
        
        try:
            with open(filename, 'w') as f:
                json.dump(metrics_data, f, indent=2)
        except Exception as e:
            print(f"Error saving metrics: {str(e)}")
            
    async def close(self) -> None:
        """关闭前刷新所有缓冲区"""
        await self._flush_trades_buffer()
        await self._flush_balances_buffer()

class PerformanceMonitor:
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.latency_metrics = {
            'order_latency': [],
            'market_data_latency': [],
            'cycle_latency': [],
            'request_latency': []
        }
        self.order_metrics = {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'timed_out_orders': 0
        }
        self.warnings = []
        self.last_warning_time = 0
    
    def add_latency(self, metric_type: str, value: float):
        """添加延迟数据"""
        if metric_type in self.latency_metrics:
            self.latency_metrics[metric_type].append(value)
            # 保持窗口大小
            if len(self.latency_metrics[metric_type]) > self.window_size:
                self.latency_metrics[metric_type] = self.latency_metrics[metric_type][-self.window_size:]
    
    def update_order_metrics(self, status: str):
        """更新订单指标"""
        self.order_metrics['total_orders'] += 1
        
        if status == 'success':
            self.order_metrics['successful_orders'] += 1
        elif status == 'timeout':
            self.order_metrics['timed_out_orders'] += 1
        else:
            self.order_metrics['failed_orders'] += 1
    
    def add_warning(self, message: str, level: str = 'warning'):
        """添加警告"""
        # 限制警告频率，避免过多警告
        current_time = time.time()
        if current_time - self.last_warning_time < 5:  # 5秒内最多一条相同警告
            # 检查是否已有相同警告
            if any(w['message'] == message for w in self.warnings[-5:]):
                return
        
        self.warnings.append({
            'timestamp': current_time,
            'message': message,
            'level': level
        })
        self.last_warning_time = current_time
        
        # 只保留最近100条警告
        if len(self.warnings) > 100:
            self.warnings = self.warnings[-100:]
    
    def get_latency_stats(self) -> Dict:
        """获取延迟统计数据"""
        stats = {}
        
        for metric_name, values in self.latency_metrics.items():
            if values:
                stats[metric_name] = {
                    'avg': statistics.mean(values),
                    'max': max(values),
                    'min': min(values),
                    'median': statistics.median(values),
                    'p95': sorted(values)[int(len(values) * 0.95)] if len(values) >= 20 else max(values),
                    'stddev': statistics.stdev(values) if len(values) > 1 else 0
                }
            else:
                stats[metric_name] = {
                    'avg': 0, 'max': 0, 'min': 0, 'median': 0, 'p95': 0, 'stddev': 0
                }
        
        return stats
    
    def get_order_metrics(self) -> Dict:
        """获取订单指标"""
        metrics = self.order_metrics.copy()
        
        # 计算订单成功率
        total = metrics['total_orders']
        metrics['success_rate'] = metrics['successful_orders'] / total if total > 0 else 0
        metrics['timeout_rate'] = metrics['timed_out_orders'] / total if total > 0 else 0
        metrics['failure_rate'] = metrics['failed_orders'] / total if total > 0 else 0
        
        return metrics
    
    def get_performance_report(self) -> Dict:
        """获取性能报告"""
        return {
            'latency': self.get_latency_stats(),
            'orders': self.get_order_metrics(),
            'warnings': self.warnings[-10:],  # 只返回最近10条警告
            'timestamp': time.time()
        }
    
    def check_performance_issues(self, latency_threshold: float = 0.5) -> List[str]:
        """检查性能问题"""
        issues = []
        
        # 检查延迟问题
        for metric_name, values in self.latency_metrics.items():
            if values and statistics.mean(values) > latency_threshold:
                issues.append(f"High {metric_name}: {statistics.mean(values):.4f}s")
        
        # 检查订单成功率
        total = self.order_metrics['total_orders']
        if total > 10:
            success_rate = self.order_metrics['successful_orders'] / total
            if success_rate < 0.8:
                issues.append(f"Low order success rate: {success_rate:.2%}")
        
        return issues 