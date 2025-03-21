"""
Trading bot configuration
"""

# Exchange API credentials
EXCHANGE_CONFIG = {
    'exchange': 'binance',  # 使用的交易所ID
    'apiKey': 'b2a2eaacacd92fe3ec31d33442287af4378adf3e429ca793986af2fc6f9297c5',  # 替换为你的API密钥
    'secret': '431eae2f6f28709901248b32a8d38a9ed419cfb4398adcd15871ef0360ec3759',  # 替换为你的密钥
    'password': None,  # 如果需要密码，请提供
    'enableRateLimit': True,  # 启用请求频率限制（强烈建议）
    'testnet': True,  # 使用测试网络
    'options': {
        'defaultType': 'future',  # 使用期货市场
        'adjustForTimeDifference': True,  # 调整服务器时间差异
        'recvWindow': 10000,  # 请求有效时间窗口（毫秒）
    },
}

# 测试网说明：
# 1. 在上方设置 'testnet': True 以使用测试网
# 2. 访问 https://testnet.binancefuture.com 创建测试网账户
# 3. 在测试网网站生成API密钥，并填入上方配置
# 4. 测试网的API密钥不能用于真实交易，反之亦然

# 注意：要获取Binance测试网API密钥：
# 1. 访问 https://testnet.binancefuture.com/
# 2. 使用邮箱注册并登录
# 3. 在交易界面中找到"API KEYS"标签页(位于图表下方的面板中)
# 4. 点击生成API密钥
# 5. 将生成的API Key和Secret Key复制到上面的配置中

# Trading parameters
TRADING_CONFIG = {
    'symbols': ['BTC/USDT', 'ETH/USDT'],  # 交易对列表
    'base_currency': 'USDT',  # 基础货币
    'position_size': 0.03,  # 增加持仓量
    'max_positions': 5,  # 增加最大持仓数
    'max_open_orders': 10,  # 增加最大订单数
    'stop_loss': 0.03,  # 减小止损比例
    'take_profit': 0.015,  # 减小止盈比例
    'max_daily_trades': 100,
    'max_daily_loss': 0.05,
    'max_drawdown': 0.15,  # 放宽最大回撤
    'cooldown_after_loss': 60,  # 减少冷却时间
    'risk_per_trade': 0.01,
    'max_daily_loss_count': 5,  # 连续亏损次数上限
}

# Strategy parameters
STRATEGY_CONFIG = {
    'timeframe': '1m',  # 时间周期
    'volume_window': 60,  # 成交量时间窗口（秒）
    'price_window': 300,  # 价格时间窗口（秒）
    'min_volume': 5,  # 最小成交量
    'min_spread': 0.0001,  # 最小价差
    'max_spread': 0.005,  # 最大价差要求
    'order_size_ratio': 1.5,  # 订单大小比例
    'min_price_change': 0.0005,  # 最小价格变化
    'trend_strength_threshold': 1.2,  # 趋势强度阈值(买卖量比例)
    'max_position_holding_time': 60,  # 最长持仓时间(秒)
    'order_timeout': 30,  # 增加订单超时时间
    'order_update_interval': 2,  # 减少更新间隔
}

# Monitoring parameters
MONITORING_CONFIG = {
    'update_interval': 600,  # 监控更新间隔(秒)
    'log_level': 'INFO',
    'save_trades': True,  # 是否保存交易记录
    'save_balance': True,  # 是否保存余额记录
    'latency_threshold': 0.5,  # 延迟警告阈值(秒)
    'performance_metrics_window': 100,  # 性能指标窗口大小
    'order_success_rate_threshold': 0.8,  # 订单成功率阈值
}

# Risk management
RISK_CONFIG = {
    'max_daily_trades': 100,  # 每日最大交易次数
    'max_position_size': 0.1,  # 最大仓位大小
    'max_drawdown': 0.1,  # 最大回撤
    'min_balance': 100,  # 最小余额要求
    'max_open_orders': 10,  # 最大挂单数量
    'max_notional_value': 1000,  # 最大名义价值(USDT)
    'max_daily_loss_count': 5,  # 连续亏损次数上限
    'cooldown_after_loss': 300,  # 连续亏损后冷却时间(秒)
}

# Performance optimization
PERFORMANCE_CONFIG = {
    'use_websocket': True,  # 使用WebSocket而非REST API
    'use_concurrent_requests': True,  # 使用并发请求
    'max_concurrent_symbols': 5,  # 最大并发处理的交易对数量
    'throttle_requests': True,  # 限制请求频率
    'request_delay': 0.1,  # 请求间隔(秒)
} 