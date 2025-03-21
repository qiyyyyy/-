# 高频交易机器人

这是一个基于CCXT框架的高频交易机器人，支持多个加密货币交易所，实现了高频做市商交易策略。该机器人能够根据市场流动性动态调整价格和交易数量，同时提供风险管理和性能监控功能。

## 功能特点

- 实现高频做市商策略，动态调整买卖价格
- 支持多个交易对并发交易
- 实时市场数据监控与分析
- 自动风险控制和资金管理
- 完整的日志记录与性能监控
- 交易数据持久化存储
- 支持测试网络和实盘环境切换
- 异步处理提高性能

## 在CentOS上安装与部署

### 系统要求

- CentOS 7/8
- Python 3.8+ 
- 网络连接稳定
- 足够的内存（推荐至少4GB RAM）

### 安装步骤

#### 1. 安装必要的系统依赖

```bash
# 更新系统
sudo yum update -y

# 安装基础工具和依赖
sudo yum install -y git wget curl gcc make openssl-devel bzip2-devel libffi-devel zlib-devel

# 安装Python开发工具
sudo yum groupinstall -y "Development Tools"
```

#### 2. 安装Python 3.8+（如果尚未安装）

```bash
# 下载Python源码
wget https://www.python.org/ftp/python/3.9.13/Python-3.9.13.tgz
tar xzf Python-3.9.13.tgz
cd Python-3.9.13

# 配置、编译和安装
./configure --enable-optimizations
make altinstall

# 确认安装成功
python3.9 --version
```

#### 3. 创建虚拟环境（可选但推荐）

```bash
# 安装虚拟环境管理工具
pip3.9 install virtualenv

# 创建并激活虚拟环境
mkdir -p ~/trading_env
cd ~/trading_env
virtualenv -p python3.9 venv
source venv/bin/activate
```

#### 4. 克隆项目

```bash
git clone https://github.com/yourusername/trading-bot.git
cd trading-bot
```

#### 5. 安装依赖

```bash
pip install -r trading_bot/requirements.txt
```

### 配置

#### 1. API密钥配置

编辑`trading_bot/config.py`文件，填入您的交易所API密钥：

```bash
# 复制默认配置文件
cp trading_bot/config.py trading_bot/config_local.py

# 编辑配置文件
vi trading_bot/config_local.py
```

在`config_local.py`中找到并修改以下部分：

```python
EXCHANGE_CONFIG = {
    'apiKey': 'YOUR_API_KEY',  # 修改为你的API密钥
    'secret': 'YOUR_SECRET_KEY',  # 修改为你的密钥
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',  # 期货交易
        'adjustForTimeDifference': True,
    }
}

# 开启测试网络（推荐先在测试环境运行）
EXCHANGE_CONFIG['testnet'] = True
```

#### 2. 交易配置

根据您的需求调整以下交易参数：

```python
TRADING_CONFIG = {
    'symbols': ['BTC/USDT', 'ETH/USDT'],  # 交易对
    'base_currency': 'USDT',
    'position_size': 0.01,  # 基础仓位大小
    'max_positions': 5,     # 最大持仓数量
    'stop_loss': 0.02,      # 止损比例
    'take_profit': 0.03,    # 止盈比例
    'max_daily_trades': 100,
    'max_daily_loss': 0.05,
    'min_balance': 100,
}
```

#### 3. 策略配置

调整策略参数以适应您的交易需求：

```python
STRATEGY_CONFIG = {
    'volume_window': 60,     # 秒
    'price_window': 30,      # 秒
    'min_spread': 0.0001,    # 最小价差
    'order_size_ratio': 1.0, # 调整订单大小的比例
    'min_price_diff_factor': 2.0,
    'trend_strength_threshold': 1.2,
    'max_position_holding_time': 60,  # 最大持仓时间（秒）
    'order_update_interval': 5,       # 订单更新间隔（秒）
}
```

### 启动机器人

#### 1. 简单启动（前台运行）

```bash
python -m trading_bot.main
```

#### 2. 使用nohup后台运行

```bash
nohup python -m trading_bot.main > trading_bot.log 2>&1 &
```

#### 3. 使用系统服务（推荐长期运行）

创建系统服务文件：

```bash
sudo vi /etc/systemd/system/trading-bot.service
```

添加以下内容：

```
[Unit]
Description=High Frequency Trading Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/trading-bot
ExecStart=/path/to/python -m trading_bot.main
Restart=on-failure
RestartSec=10
StandardOutput=append:/path/to/trading-bot/logs/output.log
StandardError=append:/path/to/trading-bot/logs/error.log

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start trading-bot
sudo systemctl enable trading-bot  # 设置开机自启
```

查看服务状态：

```bash
sudo systemctl status trading-bot
```

查看日志：

```bash
sudo journalctl -u trading-bot -f
```

### 监控与维护

#### 1. 检查交易日志

```bash
tail -f data/logs/log_YYYYMMDD.json
```

#### 2. 检查性能指标

```bash
cat data/metrics/metrics_YYYYMMDD_HHMMSS.json
```

#### 3. 停止机器人

如果使用systemd服务：

```bash
sudo systemctl stop trading-bot
```

如果使用nohup：

```bash
# 找到进程ID
ps aux | grep trading_bot

# 停止进程
kill -15 <进程ID>
```

## 性能优化建议

1. **系统调优**：
   - 增加文件描述符限制：`ulimit -n 65535`
   - 调整网络参数，减少延迟

2. **网络优化**：
   - 使用有线网络连接
   - 考虑使用云服务器靠近交易所API服务器

3. **资源监控**：
   - 安装`htop`监控系统资源：`sudo yum install htop`
   - 使用`iotop`监控磁盘IO：`sudo yum install iotop`

## 故障排除

1. **API连接问题**：
   - 检查API密钥是否正确
   - 确认网络连接是否稳定
   - 确认IP地址是否被交易所白名单允许

2. **性能问题**：
   - 检查系统负载
   - 减少同时交易的交易对数量
   - 查看`data/metrics`中的延迟指标

3. **订单执行问题**：
   - 检查账户余额是否充足
   - 确认杠杆设置是否正确
   - 查看订单日志`data/orders`

## 风险提示

加密货币交易具有高风险，请在使用本机器人时注意：

1. 仅使用可以承受损失的资金
2. 先在测试网络验证策略可行性
3. 从小仓位开始，逐步增加
4. 密切关注市场变化
5. 定期检查和调整参数
6. 设置合理的风险控制参数

## 常见错误与解决方案

### 1. `'binance' object has no attribute 'fapiPrivate_post_leverage'` 错误

**问题描述**：启动机器人时提示无法找到 `fapiPrivate_post_leverage` 方法。

**原因**：这通常是由于以下原因之一导致的：
- CCXT库版本较新，API方法名称已更改
- 未正确配置交易所类型为期货交易
- 使用了非异步的CCXT版本调用异步方法

**解决方案**：
```python
# 1. 修改代码，使用标准的set_leverage方法（首选方案）
await exchange.set_leverage(1, symbol)  # 参数：杠杆倍数, 交易对

# 2. 如果需要兼容多种交易所，使用更灵活的方法
try:
    # 首先尝试标准方法
    await exchange.set_leverage(1, symbol)
except Exception as e:
    # 回退到低级API调用
    try:
        params = {'symbol': symbol.replace('/', ''), 'leverage': 1}
        if hasattr(exchange, 'fapiPrivatePostLeverage'):
            await exchange.fapiPrivatePostLeverage(params)
        elif hasattr(exchange, 'privateFuturesPostLeverage'):
            await exchange.privateFuturesPostLeverage(params)
        else:
            logging.warning(f"无法设置杠杆，没有找到合适的方法")
    except Exception as ex:
        logging.error(f"设置杠杆失败: {str(ex)}")
```

### 2. 异步调用错误

**问题描述**：运行时出现 `"coroutine was never awaited"` 或 `"await outside of async function"` 等错误。

**原因**：将同步代码和异步代码混合使用，没有正确使用 `await` 关键字。

**解决方案**：
- 确保所有异步函数都使用 `async def` 定义
- 确保所有异步函数调用都使用 `await` 关键字
- 确保所有异步IO操作都在异步环境中运行
- 使用 `asyncio.run()` 运行异步代码入口函数

### 3. 交易所API响应缓慢或超时

**问题描述**：交易所API调用频繁失败或者响应非常缓慢。

**原因**：
- 网络连接不稳定
- 交易所服务器负载过高
- 请求频率超过限制

**解决方案**：
```python
# 1. 增加重试机制
async def fetch_with_retry(func, *args, retries=3, delay=1, **kwargs):
    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == retries - 1:
                raise
            logging.warning(f"API调用失败，{delay}秒后重试: {str(e)}")
            await asyncio.sleep(delay)
            delay *= 2  # 指数退避

# 2. 确保启用速率限制
exchange_config = {
    'enableRateLimit': True,  # 非常重要！
    # 其他配置...
}

# 3. 设置更长的超时时间
exchange_config['options']['timeout'] = 30000  # 毫秒
```

### 4. 配置文件问题

**问题描述**：机器人无法启动或加载配置失败。

**原因**：
- 配置文件格式错误
- 配置文件路径不正确
- 配置参数缺失

**解决方案**：
- 确认配置文件使用正确的格式（JSON或YAML）
- 检查配置文件中的引号、大括号、方括号等是否匹配
- 确保必需的配置项都已填写，特别是API密钥和交易所设置

### 5. 数据存储问题

**问题描述**：无法保存交易日志或者其他数据。

**原因**：
- 磁盘空间不足
- 目录权限问题
- 文件系统错误

**解决方案**：
```bash
# 检查磁盘空间
df -h

# 检查目录权限
ls -la data/

# 修复权限问题
chmod -R 755 data/
chown -R your_username:your_group data/

# 创建缺失的目录
mkdir -p data/logs data/trades data/metrics data/orders
```

### 6. "Invalid Api-Key ID" 错误

**问题描述**：启动机器人时出现 `{"code":-2008,"msg":"Invalid Api-Key ID."}` 错误。

**原因**：
- API密钥无效或已过期
- 使用了错误的API密钥（例如将现货API密钥用于期货交易）
- 使用了真实环境的API密钥，但配置为测试网环境（或反之）
- API密钥的权限不足

**解决方案**：
1. **确保使用正确的测试网API密钥**：
   - 对于期货测试网，请前往 https://testnet.binancefuture.com/ 注册并登录
   - 在交易页面中找到"API KEYS"标签（位于图表下方面板中）
   - 生成新的API密钥并复制到配置文件中

2. **确认测试网状态**：
   ```python
   # 在配置中确保已设置testnet为True
   EXCHANGE_CONFIG = {
       'testnet': True,  # 这是测试网设置
       # 其他配置...
   }
   ```

3. **检查API密钥权限**：
   - 期货测试网的API密钥需要有期货交易的权限
   - 确保API密钥没有被限制IP或其他限制

4. **资源正确关闭**：
   - 确保程序完全退出后再重新启动
   - 使用 `await exchange.close()` 明确关闭连接

5. **重新生成新的API密钥**：
   - 有时API密钥会因长时间不活动而失效
   - 尝试删除旧密钥并生成新密钥

## 许可证

MIT License 