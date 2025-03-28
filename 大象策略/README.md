# 大象策略

一个基于VNPY框架开发的高频交易策略，适用于中国A股T+1市场。该策略利用盘口中的大额买单支撑（称为"大象"）进行"先卖后买"的高频交易。

## 策略概述

### 核心思路

1. **发现大象**：在盘口中识别大额买单支撑（通常在买二档或更后档位）
2. **先卖后买**：
   - 利用已持有的股票，在大象支撑价格之上小幅卖出
   - 等待价格回调或设定时间后，以更低价格买回
   - 从价差中获取利润
3. **资金平衡**：将资金分为股票池和现金池，保持平衡运作

### 特点优势

- 适应T+1交易规则，无需隔夜持仓
- 通过"先卖后买"方式实现真正的日内高频
- 风险相对可控，有明确的止损机制
- 模块化设计，各组件功能清晰独立
- 支持网页远程监控和管理
- 集成测试模块，确保策略稳定性

## 文件结构

```
大象策略/
├── modules/                  # 策略模块目录
│   ├── __init__.py          # 模块初始化文件
│   ├── 资金管理.py           # 资金管理模块
│   ├── 大象识别.py           # 大象识别模块
│   ├── 交易执行.py           # 交易执行模块
│   ├── 风险控制.py           # 风险控制模块
│   ├── 网页管理.py           # 网页远程管理模块
│   └── 测试模块.py           # 模块测试和验证模块
├── config/                   # 配置文件目录
│   └── stocks.json          # 交易股票列表配置
├── data/                     # 数据存储目录（自动创建）
├── logs/                     # 日志存储目录（自动创建）
├── 大象策略.py               # 主策略文件
└── docs/                     # 文档目录
    ├── 安装指南.md           # 安装和部署说明
    ├── 用户手册.md           # 使用说明和参数配置
    ├── 技术文档.md           # 技术实现和数据结构
    ├── 测试指南.md           # 测试模块使用方法
    └── 风险控制.md           # 风险管理相关说明
```

## 快速开始

1. 安装VNPY框架和相关依赖
2. 将策略代码复制到VNPY策略目录
3. 配置交易参数和账户信息
4. 通过VNPY平台或命令行启动策略

## 文档索引

- [**安装指南**](docs/安装指南.md)：详细的环境搭建、依赖安装和部署步骤
- [**用户手册**](docs/用户手册.md)：日常使用说明、参数设置和账户配置
- [**技术文档**](docs/技术文档.md)：核心模块实现原理和技术细节
- [**测试指南**](docs/测试指南.md)：测试模块使用方法和结果分析
- [**风险控制**](docs/风险控制.md)：风险管理机制和应对措施

## 安装部署

### 前提条件

- VNPY 2.2.0+
- Python 3.7+
- 已有证券账户接入

### Windows安装步骤

1. **安装Python环境**
   - 访问 [Python官网](https://www.python.org/downloads/)
   - 下载并安装Python 3.9（VNPY兼容性最佳）
   - 安装时勾选"Add Python to PATH"选项

2. **安装TA-Lib（技术分析库）**
   - 访问 [TA-Lib预编译文件](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib)
   - 下载对应版本（例如：`TA_Lib‑0.4.28‑cp39‑cp39‑win_amd64.whl`）
   - 打开命令提示符，安装下载的文件：
     ```
     pip install TA_Lib‑0.4.28‑cp39‑cp39‑win_amd64.whl
     ```

3. **安装VNPY**
   - 下载VNPY源码
   - 运行安装脚本`install.bat`
   - 或使用pip安装：`pip install vnpy`

4. **部署策略**
   - 将`大象策略`文件夹复制到VNPY的策略目录中
   - 修改配置参数后开始运行

### Linux服务器安装步骤

#### 推荐服务器配置

**国内云服务商（推荐）**
1. **阿里云 ECS**
   - 配置：2核4G内存，50GB SSD云盘
   - 系统：Ubuntu 20.04 LTS

2. **腾讯云 CVM**
   - 配置：2核4G内存，50GB SSD云硬盘
   - 系统：Ubuntu 20.04 LTS

**国际云服务商**
- **DigitalOcean Droplet**：Basic Droplet，2核4GB内存

#### 安装步骤

1. **安装Python环境**
   ```bash
   # 更新系统包
   sudo apt update
   sudo apt upgrade -y

   # 安装Python和开发工具
   sudo apt install -y python3.9 python3.9-dev python3.9-venv python3-pip build-essential git

   # 创建虚拟环境
   mkdir ~/vnpy_env
   cd ~/vnpy_env
   python3.9 -m venv venv
   source venv/bin/activate
   ```

2. **安装TA-Lib依赖**
   ```bash
   # 安装依赖库
   sudo apt install -y wget

   # 下载并安装TA-Lib
   wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
   tar -xzf ta-lib-0.4.0-src.tar.gz
   cd ta-lib/
   ./configure --prefix=/usr
   make
   sudo make install

   # 安装Python绑定
   pip install ta-lib
   ```

3. **安装VNPY框架**
   ```bash
   # 克隆VNPY仓库
   git clone https://github.com/vnpy/vnpy.git
   cd vnpy

   # 安装
   bash install.sh
   ```

4. **部署大象策略**
   ```bash
   # 创建策略目录
   mkdir -p ~/vnpy/strategies/
   cd ~/vnpy/strategies/

   # 上传策略文件夹或克隆代码
   # 使用SFTP/SCP上传或:
   git clone https://github.com/your-repo/大象策略.git

   # 设置策略配置
   nano 大象策略/config/stocks.json
   # 添加您要交易的股票代码
   ```

5. **创建启动脚本**
   > 注意：`run_strategy.py`文件需要自己创建，不是现成提供的文件。它用于在Linux服务器上自动启动VNPY和大象策略。
   
   ```bash
   # 在用户主目录创建启动脚本
   cd ~
   nano run_strategy.py
   
   # 复制以下代码到文件中
   ```
   
   ```python
   from vnpy.event import EventEngine
   from vnpy.trader.engine import MainEngine
   from vnpy.trader.ui import MainWindow, create_qapp
   from vnpy.gateway.ctp import CtpGateway
   from vnpy.app.cta_strategy import CtaStrategyApp
   
   def main():
       """启动VNPY交易平台"""
       qapp = create_qapp()
       event_engine = EventEngine()
       main_engine = MainEngine(event_engine)
       
       # 添加交易接口
       main_engine.add_gateway(CtpGateway)
       
       # 添加应用
       main_engine.add_app(CtaStrategyApp)
       
       # 加载和初始化策略
       cta_engine = main_engine.get_engine("cta_strategy")
       cta_engine.init_engine()
       cta_engine.add_strategy("大象策略", "大象策略", {})
       cta_engine.init_all_strategies()
       cta_engine.start_all_strategies()
       
       print("策略已启动，运行中...")
       
       # 保持运行
       qapp.exec_()

   if __name__ == "__main__":
       main()
   ```
   
   ```bash
   # 保存并退出编辑器（在nano中按Ctrl+X，然后按Y确认保存）
   # 赋予脚本执行权限
   chmod +x ~/run_strategy.py
   ```

6. **服务器后台运行**
   ```bash
   # 创建启动脚本
   nano ~/run_strategy.py
   
   # 粘贴以下代码
   from vnpy.event import EventEngine
   from vnpy.trader.engine import MainEngine
   from vnpy.trader.ui import MainWindow, create_qapp
   from vnpy.gateway.ctp import CtpGateway
   from vnpy.app.cta_strategy import CtaStrategyApp
   
   def main():
       """启动VNPY交易平台"""
       qapp = create_qapp()
       event_engine = EventEngine()
       main_engine = MainEngine(event_engine)
       
       # 添加交易接口
       main_engine.add_gateway(CtpGateway)
       
       # 添加应用
       main_engine.add_app(CtaStrategyApp)
       
       # 加载和初始化策略
       cta_engine = main_engine.get_engine("cta_strategy")
       cta_engine.init_engine()
       cta_engine.add_strategy("大象策略", "大象策略", {})
       cta_engine.init_all_strategies()
       cta_engine.start_all_strategies()
       
       print("策略已启动，运行中...")
       
       # 保持运行
       qapp.exec_()

   if __name__ == "__main__":
       main()
   
   # 保存退出
   
   # 使用nohup后台运行
   nohup python ~/run_strategy.py > strategy_log.txt 2>&1 &
   ```

7. **设置自动重启服务**
   ```bash
   sudo nano /etc/systemd/system/vnpy-strategy.service
   
   # 添加以下内容
   [Unit]
   Description=VNPY Trading Strategy
   After=network.target
   
   [Service]
   User=your_username
   WorkingDirectory=/home/your_username/vnpy
   ExecStart=/home/your_username/vnpy_env/venv/bin/python /home/your_username/run_strategy.py
   Restart=on-failure
   RestartSec=5s
   
   [Install]
   WantedBy=multi-user.target
   
   # 保存退出
   
   # 启用服务
   sudo systemctl enable vnpy-strategy
   sudo systemctl start vnpy-strategy
   ```

8. **开放网页管理端口**
   ```bash
   sudo ufw allow 8088/tcp
   ```

9. **远程访问网页管理界面**
   - 通过SSH隧道安全访问：
     ```bash
     # 在本地电脑执行
     ssh -L 8088:localhost:8088 username@your_server_ip
     ```
   - 然后在本地浏览器访问：http://localhost:8088

## 核心参数说明

### 大象识别参数

- **大象委托量阈值**：判定为大象的最小委托金额（元）
- **大象价差阈值**：大象与卖一价的最大价差百分比
- **大象确认次数**：连续确认大象存在的次数要求
- **大象稳定时间**：大象稳定存在的最小秒数

### 交易执行参数

- **价格偏移量**：最小价格变动单位
- **卖出偏移量倍数**：卖出价高于大象价格的偏移量倍数
- **买入偏移量倍数**：买入价高于大象价格的偏移量倍数
- **等待时间**：等待订单成交的最长时间(秒)
- **冷却时间**：同一股票交易后的冷却时间(秒)

### 资金管理参数

- **股票池比例**：股票资金池目标比例
- **买回保障金比例**：现金池中作为买回保障的比例
- **单股最大仓位比例**：单只股票最大持仓占总资产比例

### 风险控制参数

- **单笔最大亏损比例**：单笔交易最大亏损占总资产比例
- **单股最大亏损比例**：单只股票日内最大亏损占总资产比例
- **日内最大亏损比例**：日内最大总亏损占总资产比例
- **单股最大交易次数**：单只股票日内最大交易次数
- **总交易次数限制**：日内总交易次数限制

### 网页管理参数

- **启用网页管理**：是否启用网页管理功能
- **网页管理端口**：网页管理服务器端口号
- **自动打开浏览器**：启动时是否自动打开管理界面

## T+1规则处理机制

大象策略专为A股T+1交易规则设计，能够精确区分当天买入的股票（不可卖出）和之前持有的股票（可卖出），具体实现如下：

### 1. 持仓记录设计

资金管理模块维护详细的持仓记录，关键字段包括：

```python
# 持仓记录结构示例
self.持仓 = {
    "股票代码1": {
        "总数量": 1000,         # 该股票的总持仓数量
        "可交易数量": 800,      # 当天可卖出的数量
        "冻结数量": 200,        # 当天买入的数量（T+1规则下被冻结）
        "买入时间": {           # 记录每笔买入的时间，用于自动解冻
            "批次1": {"数量": 200, "时间": 买入时间1},
            "批次2": {"数量": 800, "时间": 买入时间2}
        },
        "成本": 10.5,           # 平均成本价
        # 其他信息...
    },
    # 其他股票...
}
```

### 2. 买入股票处理

当执行买入操作时，系统会：

1. 更新该股票的总持仓数量
2. 将新买入的股票标记为"冻结数量"
3. 记录买入时间，用于后续确定解冻时机

```python
# 买入股票后的处理逻辑
def 更新买入记录(self, 股票代码, 买入数量, 买入价格):
    if 股票代码 not in self.持仓:
        self.持仓[股票代码] = {
            "总数量": 0, 
            "可交易数量": 0, 
            "冻结数量": 0, 
            "买入时间": {},
            "成本": 0
        }
    
    # 更新持仓数量
    self.持仓[股票代码]["总数量"] += 买入数量
    self.持仓[股票代码]["冻结数量"] += 买入数量
    
    # 记录买入时间
    批次ID = f"批次{len(self.持仓[股票代码]['买入时间']) + 1}"
    self.持仓[股票代码]["买入时间"][批次ID] = {
        "数量": 买入数量,
        "时间": datetime.now()
    }
    
    # 更新成本价
    # ... 成本计算逻辑 ...
```

### 3. 卖出前检查

每次准备卖出股票时，系统会检查可交易数量，确保只操作非冻结部分：

```python
# 卖出前检查可用数量
def 检查可卖数量(self, 股票代码, 请求数量):
    持仓信息 = self.持仓.get(股票代码, None)
    if not 持仓信息:
        return 0
    
    # 返回可交易数量和请求数量中的较小值
    return min(持仓信息["可交易数量"], 请求数量)
```

### 4. 交易日切换处理

系统在每个交易日开始时，会自动将前一交易日买入的股票解冻：

```python
# 交易日开始时更新持仓状态
def 日初更新持仓状态(self):
    今天 = datetime.now().date()
    for 股票代码, 持仓信息 in self.持仓.items():
        解冻数量 = 0
        待删除批次 = []
        
        # 检查每笔买入记录
        for 批次ID, 买入记录 in 持仓信息["买入时间"].items():
            买入日期 = 买入记录["时间"].date()
            if 买入日期 < 今天:  # 前一交易日买入的，可以解冻
                解冻数量 += 买入记录["数量"]
                待删除批次.append(批次ID)
        
        # 更新可交易和冻结数量
        持仓信息["可交易数量"] += 解冻数量
        持仓信息["冻结数量"] -= 解冻数量
        
        # 删除已解冻的买入记录
        for 批次ID in 待删除批次:
            del 持仓信息["买入时间"][批次ID]
```

### 5. 持久化存储

持仓状态会保存到本地文件，确保策略重启后仍能正确识别T+1状态：

```python
# 保存持仓状态
def 保存持仓数据(self):
    with open(self.持仓数据文件, 'w', encoding='utf-8') as f:
        json.dump(self.持仓, f, ensure_ascii=False, default=self._json序列化处理)

# 加载持仓状态
def 加载持仓数据(self):
    if os.path.exists(self.持仓数据文件):
        with open(self.持仓数据文件, 'r', encoding='utf-8') as f:
            持仓数据 = json.load(f)
            # 处理时间反序列化等...
            self.持仓 = 持仓数据
```

通过这种精确的持仓管理机制，大象策略能够严格遵守T+1交易规则，同时最大化利用可交易资金进行高频操作。策略的"先卖后买"模式也正是建立在对T+1规则的深度适应之上，确保了交易的合规性和高效性。

## 参数设置方法

策略参数可以通过以下几种方式进行设置和修改：

### 1. 修改主策略文件

主策略文件位于 `大象策略/大象策略.py`，其中定义了所有交易参数的默认值：

```python
# 以下是主策略文件中的参数定义示例（实际参数可能有所不同）
class 大象策略(CtaTemplate):
    # 策略参数
    # 大象识别参数
    大象委托量阈值 = 1000000  # 单位：元
    大象价差阈值 = 0.3  # 百分比
    大象确认次数 = 3
    大象稳定时间 = 5  # 秒
    
    # 交易执行参数
    价格偏移量 = 0.01
    卖出偏移量倍数 = 2
    买入偏移量倍数 = 1
    等待时间 = 30  # 秒
    冷却时间 = 60  # 秒
    
    # 其他参数...
```

直接编辑此文件可以永久修改默认参数值。修改后需要重新启动策略使其生效。

### 2. 通过VNPY图形界面设置

如果使用VNPY图形界面加载策略：

1. 在VNPY主界面中，选择"CTA策略"应用
2. 点击"添加策略"按钮
3. 选择"大象策略"后，会显示参数设置界面
4. 修改所需参数，点击"确定"保存

这种方式适合在策略首次加载时设置参数。

### 3. 通过网页管理界面设置

如果启用了网页管理功能：

1. 在浏览器中访问 `http://localhost:8088`（或设置的其他端口）
2. 登录后进入"参数设置"页面
3. 修改参数值并保存

网页界面的优点是可以在策略运行过程中实时调整参数，无需重启策略。这对于参数优化和紧急调整非常有用。

### 4. 配置文件设置（高级用户）

对于需要自动化部署的高级用户，可以创建JSON格式的参数配置文件：

```bash
# 创建参数配置文件
nano ~/vnpy/strategies/大象策略_config.json
```

```json
{
  "大象委托量阈值": 1200000,
  "大象价差阈值": 0.25,
  "大象确认次数": 4,
  "股票池比例": 0.5,
  "单股最大仓位比例": 0.1
  // 其他参数...
}
```

然后在启动脚本中加载此配置：

```python
# 在run_strategy.py中修改
cta_engine.add_strategy("大象策略", "大象策略", load_json("~/vnpy/strategies/大象策略_config.json"))
```

这种方式适合需要批量部署或经常切换不同参数组合的场景。

## 交易账户配置

运行策略前，需要配置交易所账户以接入实际市场。VNPY框架支持多种交易接口，以下是配置方法：

### 通过图形界面配置（Windows用户推荐）

1. **启动VNPY主界面**
   ```
   cd vnpy安装目录
   python run.py
   ```

2. **添加交易接口**
   - 点击主界面上的"系统"菜单
   - 选择"连接"选项
   - 从弹出窗口中选择对应的证券接口（如CTP、XTP等）
   - 点击"添加"按钮

3. **填写账户信息**
   - 用户名/账号
   - 密码
   - 经纪商ID（如适用）
   - 交易服务器地址
   - 行情服务器地址
   - 产品信息
   - 授权编码（如需要）

4. **连接验证**
   - 填写完成后点击"连接"按钮
   - 连接成功后状态会显示为"已连接"
   - 在"交易"选项卡可查看账户资产和持仓信息

### 通过配置文件设置（Linux服务器推荐）

1. **创建配置目录和配置文件**
   ```bash
   mkdir -p ~/vnpy/config
   nano ~/vnpy/config/vt_setting.json
   ```

2. **添加账户配置信息**
   ```json
   {
     "font.family": "微软雅黑",
     "font.size": 12,
     "CTP": [
       {
         "用户名": "您的交易账号",
         "密码": "您的密码",
         "经纪商代码": "您的经纪商ID",
         "交易服务器": "交易服务器地址",
         "行情服务器": "行情服务器地址",
         "产品名称": "simnow_client_test",
         "授权编码": "0000000000000000"
       }
     ]
   }
   ```

3. **在启动脚本中添加自动连接代码**
   ```python
   # 在run_strategy.py的main函数中添加
   # 添加交易接口
   main_engine.add_gateway(CtpGateway)
   
   # 自动连接账户
   main_engine.connect(
       "CTP",  # 根据实际使用的接口更改
       setting={
           "用户名": "您的交易账号",
           "密码": "您的密码",
           "经纪商代码": "您的经纪商ID",
           "交易服务器": "交易服务器地址",
           "行情服务器": "行情服务器地址",
           "产品名称": "simnow_client_test",
           "授权编码": "0000000000000000"
       }
   )
   ```

### 常见交易接口参数说明

1. **CTP接口**（中国期货市场）
   - 用户名：期货账户号
   - 密码：交易密码
   - 经纪商代码：期货公司提供的经纪商ID
   - 交易/行情服务器：期货公司提供的服务器地址

2. **XTP接口**（国内证券市场）
   - 客户号：券商提供的资金账号
   - 密码：交易密码
   - 行情/交易地址：券商提供的服务器地址和端口
   - 证书文件路径：认证证书的本地路径

3. **其他证券接口**
   - 根据接口类型和券商要求提供相应信息
   - 详情可参考VNPY官方文档

### 测试账户连接

1. **查看连接日志**
   ```bash
   # Linux环境
   tail -f ~/strategy_log.txt
   
   # Windows环境
   # 查看VNPY主界面日志区域
   ```

2. **验证账户信息**
   - 检查账户余额和持仓信息是否正确显示
   - 确认可以接收行情数据
   - 可进行小额测试交易验证（谨慎操作）

> **注意**：首次使用实盘账户交易时，建议先使用仿真环境测试策略，确认无误后再切换至实盘。使用交易账户必须遵守相关交易所规则和法律法规。

## 网页管理功能

策略提供了网页远程管理功能，可通过浏览器访问进行监控和控制：

1. **首页**：显示策略概览和最近交易
2. **策略统计**：展示资金统计和风控状态
3. **交易记录**：查看历史交易记录
4. **参数设置**：远程调整策略参数
5. **运行日志**：实时查看运行日志

默认访问地址: `http://localhost:8088`

## 测试模块

策略内置测试模块，用于验证各个功能模块的正确性：

1. **资金管理测试**：验证资金分配和持仓管理
2. **大象识别测试**：测试大象识别和跟踪逻辑
3. **交易执行测试**：检查订单管理和执行流程
4. **风险控制测试**：验证风控规则和限制
5. **网页管理测试**：测试网页服务功能

运行测试方法：
```python
# 在策略初始化后运行
策略实例._运行测试()
```

## 使用注意事项

1. **初始持仓**：策略需要预先持有一定数量的股票才能开始高频交易
2. **参数调整**：根据个人风险偏好和市场情况调整参数
3. **风险控制**：合理设置止损条件，避免过度交易
4. **股票选择**：优先选择流动性好、波动适中的股票
5. **网络要求**：使用网页管理功能时确保网络稳定
6. **服务器选择**：如果使用云服务器，选择低延迟、高稳定性的配置
7. **数据备份**：定期备份交易数据和配置文件

## 策略风险

- 如果大象支撑突然消失，可能导致无法按预期价格买回
- 频繁交易会产生较高的交易成本
- 在剧烈波动的市场中风险较大

## 免责声明

本策略仅供学习和研究使用，不构成投资建议。使用本策略进行实盘交易的风险由使用者自行承担。 