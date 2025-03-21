"""
Main program for trading bot
"""
import asyncio
import signal
import sys
import traceback
from typing import Dict
import yaml
from trading_bot.config import EXCHANGE_CONFIG, TRADING_CONFIG, STRATEGY_CONFIG
from trading_bot.strategy import HighFrequencyStrategy
from trading_bot.utils import Logger, handle_api_error
import os
import datetime
import platform

# 修复Windows上的aiodns问题
def setup_windows_event_loop():
    if platform.system() == 'Windows':
        try:
            import selectors
            selector = selectors.SelectSelector()
            loop = asyncio.SelectorEventLoop(selector)
            asyncio.set_event_loop(loop)
            return True
        except Exception as e:
            print(f"Warning: Failed to set Windows event loop: {str(e)}")
            return False
    return True

class TradingBot:
    def __init__(self):
        # 创建logs目录
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # 创建带时间戳的日志文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(logs_dir, f'tradingbot_{timestamp}.log')
        
        self.logger = Logger('TradingBot', log_file=log_file)
        self.logger.info(f"日志文件已创建: {log_file}")
        self.strategy = None
        self.running = False
    
    def load_config(self, config_file: str = None) -> Dict:
        """加载配置文件"""
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
            except Exception as e:
                self.logger.error(f"Failed to load config file: {str(e)}")
                config = {}
        else:
            config = {}
        
        # 合并默认配置和用户配置
        exchange_config = {**EXCHANGE_CONFIG, **config.get('exchange', {})}
        trading_config = {**TRADING_CONFIG, **config.get('trading', {})}
        strategy_config = {**STRATEGY_CONFIG, **config.get('strategy', {})}
        
        return {
            'exchange': exchange_config,
            'trading': trading_config,
            'strategy': strategy_config
        }
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start_async(self, config_file: str = None):
        """异步启动交易机器人"""
        try:
            # 加载配置
            config = self.load_config(config_file)
            
            # 显示关键配置信息
            self.logger.info(f"交易对: {config['trading'].get('symbols', [])}")
            self.logger.info(f"交易所: {config['exchange'].get('exchange', 'unknown')}")
            
            # 创建策略实例
            self.strategy = HighFrequencyStrategy(
                config['exchange'],
                config['trading'],
                config['strategy']
            )
            
            # 设置信号处理器
            self.setup_signal_handlers()
            
            # 启动策略
            self.running = True
            self.logger.info("正在启动交易机器人...")
            
            # 检查API密钥是否为占位符
            api_key = config['exchange'].get('apiKey', '')
            if not api_key or api_key == 'YOUR_API_KEY_HERE':
                self.logger.error("API密钥未配置或使用了默认占位符。请在config.py中设置有效的API密钥。")
                await self.stop_async()
                return
                
            try:
                await self.strategy.run_async()
            except Exception as e:
                error_msg = str(e)
                
                # 检查常见API错误
                if "Invalid Api-Key ID" in error_msg or "-2008" in error_msg:
                    self.logger.error("API密钥无效。如果您正在使用测试网，请确保：")
                    self.logger.error("1. 使用了正确的测试网API密钥（不是主网的）")
                    self.logger.error("2. 在config.py中将'testnet'设置为True")
                    self.logger.error("3. 测试网API密钥具有正确的权限")
                    self.logger.error("请访问 https://testnet.binancefuture.com 重新生成API密钥")
                else:
                    # 使用通用错误处理
                    await handle_api_error(
                        e, config['exchange'].get('exchange', 'unknown'), 
                        "运行交易策略", None
                    )
                    
                # 记录详细的错误信息和堆栈跟踪
                self.logger.error(f"策略运行失败: {error_msg}")
                self.logger.debug(f"错误堆栈:\n{traceback.format_exc()}")
                
                await self.stop_async()
                
        except Exception as e:
            self.logger.error(f"启动交易机器人失败: {str(e)}")
            self.logger.debug(f"错误堆栈:\n{traceback.format_exc()}")
            await self.stop_async()
    
    def start(self, config_file: str = None):
        """启动交易机器人（非异步入口）"""
        try:
            # 设置Windows事件循环
            if platform.system() == 'Windows':
                self.logger.info("检测到Windows系统，设置SelectorEventLoop")
                setup_windows_event_loop()
                
            asyncio.run(self.start_async(config_file))
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received, stopping bot...")
        except Exception as e:
            self.logger.error(f"Error in main loop: {str(e)}")
    
    async def stop_async(self):
        """异步停止交易机器人"""
        self.running = False
        self.logger.info("Stopping trading bot...")
        if self.strategy:
            # 确保关闭交易所连接
            try:
                if hasattr(self.strategy, 'exchange') and self.strategy.exchange:
                    await self.strategy.exchange.close()
                    self.logger.info("Exchange connection closed")
                
                if hasattr(self.strategy, 'data_storage') and self.strategy.data_storage:
                    await self.strategy.data_storage.close()
                    self.logger.info("Data storage closed")
            except Exception as e:
                self.logger.error(f"Error closing resources: {str(e)}")
    
    def stop(self):
        """停止交易机器人"""
        # 创建新的事件循环来运行异步关闭函数
        try:
            # 尝试在当前事件循环中执行
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果循环正在运行，创建任务而不是等待
                self.logger.info("Adding stop task to running event loop")
                loop.create_task(self.stop_async())
            else:
                # 如果循环没有运行，直接运行stop_async
                self.logger.info("Running stop_async in current event loop")
                loop.run_until_complete(self.stop_async())
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            self.logger.info("Creating new event loop for shutdown")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.stop_async())
                loop.close()
            except Exception as e:
                self.logger.error(f"Failed to close resources properly: {str(e)}")
        
        # 在异步关闭后退出
        sys.exit(0)

def main():
    """主函数"""
    # 为Windows用户设置事件循环
    setup_windows_event_loop()
    
    bot = TradingBot()
    try:
        bot.start()
    except Exception as e:
        print(f"Fatal error in main program: {str(e)}")
        # 确保在致命错误时也能尝试优雅关闭
        bot.stop()

if __name__ == "__main__":
    main() 