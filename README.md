
# 大象策略安装与调参说明文档

## 前言

本文档为零基础用户提供在CentOS系统上安装、配置和调整大象策略的详细指南。文档采用步骤式说明，尽量避免使用专业术语，每个命令都有详细解释。

## 目录

1. [系统准备](#1-系统准备)
2. [安装Python环境](#2-安装python环境)
3. [安装大象策略](#3-安装大象策略)
4. [配置大象策略](#4-配置大象策略)
   - [4.1 创建必要的目录](#41-创建必要的目录)
   - [4.2 创建全局配置文件](#42-创建全局配置文件)
   - [4.3 创建股票列表文件](#43-创建股票列表文件)
   - [4.4 创建品种特定配置文件](#44-创建品种特定配置文件)
5. [启动策略](#5-启动策略)
6. [参数调整指南](#6-参数调整指南)
   - [6.1 全局参数调整](#61-全局参数调整)
   - [6.2 品种特定参数调整](#62-品种特定参数调整)
7. [日常维护](#7-日常维护)
8. [常见问题解答](#8-常见问题解答)

## 1. 系统准备

### 1.1 确认系统配置

大象策略推荐使用以下配置：
- CentOS 7.x 或 8.x 系统（推荐8.x）
- 至少2核CPU
- 至少4GB内存
- 至少50GB硬盘空间

### 1.2 准备系统环境

打开终端（黑色命令窗口），输入以下命令更新系统：

```bash
sudo yum update -y
```
> 这个命令会更新系统上的所有软件包到最新版本。命令执行时会要求输入管理员密码。

安装必要的系统工具：

```bash
sudo yum install -y wget git vim make gcc openssl-devel bzip2-devel libffi-devel zlib-devel
```
> 这个命令安装了编译和运行程序必需的基础工具和库。

## 2. 安装Python环境

大象策略需要Python 3.8及以上版本才能正常运行。

### 2.1 安装Python 3.8

```bash
# 下载Python 3.8安装包
cd /tmp
wget https://www.python.org/ftp/python/3.8.12/Python-3.8.12.tgz

# 解压安装包
tar -xzf Python-3.8.12.tgz
cd Python-3.8.12

# 配置Python安装
./configure --enable-optimizations

# 编译并安装Python（这一步可能需要几分钟时间）
sudo make altinstall

# 检查Python是否安装成功
python3.8 --version
```
> 如果显示Python的版本号（如Python 3.8.12），说明安装成功了。

### 2.2 创建独立的Python环境

创建一个专门的环境来运行大象策略，这样可以避免与系统其他程序冲突：

```bash
# 安装虚拟环境工具
sudo pip3.8 install virtualenv

# 创建项目目录
mkdir -p ~/elephant-strategy
cd ~/elephant-strategy

# 创建虚拟环境
python3.8 -m venv venv

# 激活虚拟环境（每次使用大象策略前都需要执行这一步）
source venv/bin/activate
```
> 当看到命令提示符前面出现`(venv)`字样时，表示成功进入虚拟环境。

## 3. 安装大象策略

### 3.1 获取大象策略代码

有两种方式获取大象策略代码：

**方式一：使用Git从代码仓库下载**
```bash
# 确保你在elephant-strategy目录下
cd ~/elephant-strategy

# 克隆代码仓库
git clone https://github.com/xxx/大象策略.git

# 进入大象策略目录
cd 大象策略
```

**方式二：手动上传代码**
如果你已有大象策略的代码包，可以通过FTP等工具上传到服务器的`~/elephant-strategy`目录下，然后解压。

### 3.2 安装依赖包

```bash
# 确保已激活虚拟环境，提示符前应有(venv)
# 如果没有，执行: source ~/elephant-strategy/venv/bin/activate

# 安装大象策略依赖
pip install pandas numpy matplotlib ta-lib vnpy
```
> 这些是大象策略运行所需的主要库。安装过程可能需要几分钟时间。

## 4. 配置大象策略

### 4.1 创建必要的目录

```bash
# 创建配置、日志和数据目录
mkdir -p ~/elephant-strategy/大象策略/modules/config
mkdir -p ~/elephant-strategy/大象策略/logs
mkdir -p ~/elephant-strategy/大象策略/data
```

### 4.2 创建全局配置文件

创建并编辑全局参数文件：

```bash
# 创建并打开文件
vim ~/elephant-strategy/大象策略/modules/config/global_params.json
```

在打开的编辑器中输入以下内容（按i键进入编辑模式）：

```json
{
  "大象识别": {
    "大象委托量阈值": 1000000.0,
    "大象价差阈值": 3,
    "大象确认次数": 3,
    "大象稳定时间": 5,
    "启用卖单识别": true,
    "卖单委托量阈值": 1200000.0,
    "卖单价差阈值": 3,
    "跳过买一价": false,
    "远距大象委托量倍数": 1.5,
    "价差分界点": 1
  },
  "交易执行": {
    "价格偏移量": 0.01,
    "等待时间": 30,
    "冷却时间": 300,
    "调戏交易量": 100
  },
  "风险控制": {
    "单笔最大亏损比例": 0.01,
    "单股最大亏损比例": 0.03,
    "日内最大亏损比例": 0.05,
    "单股最大交易次数": 50,
    "总交易次数限制": 200
  },
  "资金管理": {
    "单股最大仓位比例": 0.1,
    "最大持仓比例": 0.8
  }
}
```

输入完成后，按Esc键退出编辑模式，然后输入`:wq`保存并退出。

> 这个文件包含了策略的全局设置参数，适用于所有股票。

### 4.3 创建股票列表文件

创建并编辑股票列表文件：

```bash
# 创建并打开文件
vim ~/elephant-strategy/大象策略/modules/config/stocks.json
```

在编辑器中输入以下内容（示例股票代码，请根据实际需求修改）：

```json
["000001", "600000", "600036"]
```

输入完成后，按Esc键，然后输入`:wq`保存并退出。

> 这个文件包含了策略将要交易的股票代码列表。

### 4.4 创建品种特定配置文件

大象策略允许为每个股票单独设置参数，这对于不同特性的股票非常有用。例如，你可能想对流动性高的大盘股使用更高的委托量阈值，而对中小盘股使用更小的阈值。

#### 4.4.1 创建品种参数文件

```bash
# 创建并打开品种参数文件
vim ~/elephant-strategy/大象策略/modules/config/symbol_params.json
```

在编辑器中输入以下内容（示例配置）：

```json
{
  "000001": {
    "大象识别": {
      "大象委托量阈值": 2000000.0,
      "大象价差阈值": 2,
      "启用卖单识别": true
    },
    "交易执行": {
      "价格偏移量": 0.005,
      "调戏交易量": 200
    },
    "风险控制": {
      "单股最大交易次数": 30
    }
  },
  "600000": {
    "大象识别": {
      "大象委托量阈值": 1500000.0,
      "跳过买一价": true
    },
    "资金管理": {
      "单股最大仓位比例": 0.15
    }
  },
  "600036": {
    "大象识别": {
      "大象委托量阈值": 3000000.0,
      "大象确认次数": 4
    },
    "风险控制": {
      "单笔最大亏损比例": 0.015
    }
  }
}
```

输入完成后，按Esc键，然后输入`:wq`保存并退出。

> 这个文件指定了每个股票的特定参数。你只需要指定与全局参数不同的设置，其余参数会自动使用全局设置。

#### 4.4.2 品种参数文件格式说明

品种参数文件是一个JSON格式的文件，基本结构如下：

```
{
  "股票代码1": {
    "模块名1": {
      "参数1": 值1,
      "参数2": 值2
    },
    "模块名2": {
      "参数3": 值3
    }
  },
  "股票代码2": {
    ...
  }
}
```

其中：
- **股票代码**：如"000001"、"600000"等
- **模块名**：可以是"大象识别"、"交易执行"、"风险控制"或"资金管理"
- **参数**：模块下的具体参数名，必须与全局参数文件中的名称一致
- **值**：参数的具体数值，可以是数字、字符串或布尔值（true/false）

#### 4.4.3 配置规则

品种特定配置的使用规则：

1. 只有在品种参数文件中明确指定的参数才会覆盖全局参数
2. 同一股票可以同时设置多个模块的多个参数
3. 不同股票可以设置不同的参数
4. 如果某股票没有在品种参数文件中出现，则该股票使用全局参数
5. 品种参数中可以只指定部分参数，未指定的参数仍使用全局参数

## 5. 启动策略

### 5.1 创建启动脚本

为了方便启动大象策略，我们创建一个专门的启动脚本：

```bash
# 创建并打开启动脚本文件
vim ~/elephant-strategy/start_elephant.sh
```

在编辑器中输入以下内容：

```bash
#!/bin/bash
# 大象策略启动脚本

# 显示日期和时间
echo "==================================="
echo "启动大象策略 - $(date)"
echo "==================================="

# 激活虚拟环境
source ~/elephant-strategy/venv/bin/activate

# 切换到大象策略目录
cd ~/elephant-strategy/大象策略

# 启动策略
python 运行测试.py
```

保存并退出（按Esc，然后输入`:wq`）。

给脚本添加执行权限：

```bash
chmod +x ~/elephant-strategy/start_elephant.sh
```

### 5.2 启动策略

有两种方式启动策略：

**方式一：直接启动（前台运行）**

```bash
~/elephant-strategy/start_elephant.sh
```
> 这种方式会在当前终端窗口运行策略，关闭终端会导致策略停止。

**方式二：后台运行**

```bash
# 切换到策略目录
cd ~/elephant-strategy

# 后台启动策略，并将输出保存到日志文件
nohup ./start_elephant.sh > 大象策略/logs/策略运行.log 2>&1 &

# 查看策略是否成功启动
ps -ef | grep python
```
> 使用这种方式，即使关闭终端，策略也会继续在后台运行。

## 6. 参数调整指南

### 6.1 全局参数调整

全局参数可以通过修改`global_params.json`文件来调整。以下是主要参数的解释和调整建议：

#### 6.1.1 大象识别参数

- **大象委托量阈值**
  - **作用**：决定多大的委托量才被视为"大象"
  - **建议值**：1,000,000元到5,000,000元之间
  - **调整方法**：
    - 如果想捕捉更多的交易机会，可以把阈值调低
    - 如果发现策略交易过于频繁，可以把阈值调高

- **大象确认次数**
  - **作用**：连续多少次确认才认为大象是稳定的
  - **建议值**：2到5次之间
  - **调整方法**：
    - 数值越小，反应越快但可能误报
    - 数值越大，越准确但可能错过机会

#### 6.1.2 交易执行参数

- **价格偏移量**
  - **作用**：下单价格相对于行情的偏移比例
  - **建议值**：0.001到0.02之间
  - **调整方法**：
    - 数值越小，价格越接近行情，但可能不容易成交
    - 数值越大，成交几率越高，但成交价格会更差

- **冷却时间**
  - **作用**：每次交易后需要等待多少秒才能再次交易
  - **建议值**：60到600秒之间
  - **调整方法**：
    - 减少该值会增加交易频率
    - 增加该值会降低交易频率，更加谨慎

#### 6.1.3 风险控制参数

- **单笔最大亏损比例**
  - **作用**：单笔交易允许的最大亏损比例
  - **建议值**：0.005到0.02之间
  - **调整方法**：
    - 降低该值会使策略更加保守，更早止损
    - 提高该值会使策略更加激进，允许更大波动

- **日内最大亏损比例**
  - **作用**：单日允许的最大亏损比例，超过后停止交易
  - **建议值**：0.03到0.07之间
  - **调整方法**：
    - 降低该值会限制单日亏损，但可能错过反弹机会
    - 提高该值会允许更大的单日波动

### 6.2 品种特定参数调整

品种特定参数可以通过修改`symbol_params.json`文件来调整。以下是一些常见场景下的品种特定参数调整建议：

#### 6.2.1 根据股票市值调整

**大市值股票**（如金融、石油类）：
```json
"601398": {
  "大象识别": {
    "大象委托量阈值": 3000000.0,
    "卖单委托量阈值": 3500000.0
  },
  "交易执行": {
    "调戏交易量": 300
  }
}
```
> 大市值股票通常流动性较好，需要更高的委托量阈值和交易量。

**中小市值股票**（如科技、消费类）：
```json
"300059": {
  "大象识别": {
    "大象委托量阈值": 800000.0,
    "卖单委托量阈值": 1000000.0
  },
  "交易执行": {
    "调戏交易量": 50,
    "价格偏移量": 0.015
  }
}
```
> 中小市值股票流动性相对较差，可以使用较低的委托量阈值，但需要更大的价格偏移量。

#### 6.2.2 根据股票波动性调整

**高波动性股票**：
```json
"000688": {
  "大象识别": {
    "大象确认次数": 4,
    "大象稳定时间": 7
  },
  "风险控制": {
    "单笔最大亏损比例": 0.02,
    "单股最大亏损比例": 0.04
  }
}
```
> 波动性较大的股票需要更严格的确认条件，但可适当放宽风险控制参数。

**低波动性股票**：
```json
"601088": {
  "大象识别": {
    "大象确认次数": 2,
    "大象稳定时间": 3
  },
  "交易执行": {
    "价格偏移量": 0.005
  }
}
```
> 波动性低的股票可以使用更宽松的确认条件和更小的价格偏移量。

#### 6.2.3 根据交易时段调整

对于早盘和尾盘特征明显的股票，可以创建多个配置文件，在不同时间段使用不同的配置：

**早盘配置**（可在启动脚本中指定）：
```json
"600519": {
  "大象识别": {
    "大象委托量阈值": 2000000.0,
    "跳过买一价": true
  },
  "风险控制": {
    "单股最大交易次数": 20
  }
}
```

**尾盘配置**（可在下午切换）：
```json
"600519": {
  "大象识别": {
    "大象委托量阈值": 1500000.0,
    "跳过买一价": false
  },
  "风险控制": {
    "单股最大交易次数": 10
  }
}
```

#### 6.2.4 修改品种参数的方法

1. **手动修改**：
```bash
vim ~/elephant-strategy/大象策略/modules/config/symbol_params.json
```

2. **通过脚本修改**（适合频繁调整）：
可以创建一个简单的参数调整脚本，例如：

```bash
# 创建参数调整脚本
vim ~/elephant-strategy/adjust_params.sh
```

在脚本中添加：
```bash
#!/bin/bash
# 参数调整脚本

# 股票代码
STOCK_CODE=$1
# 参数模块
MODULE=$2
# 参数名称
PARAM_NAME=$3
# 参数值
PARAM_VALUE=$4

# 配置文件路径
CONFIG_FILE=~/elephant-strategy/大象策略/modules/config/symbol_params.json

# 使用jq工具修改JSON配置（需要先安装jq: sudo yum install -y jq）
if [ ! -f $CONFIG_FILE ]; then
  echo "{}" > $CONFIG_FILE
fi

# 确保股票代码节点存在
if ! jq -e ".[\"$STOCK_CODE\"]" $CONFIG_FILE > /dev/null 2>&1; then
  jq ".[\"$STOCK_CODE\"] = {}" $CONFIG_FILE > temp.json && mv temp.json $CONFIG_FILE
fi

# 确保模块节点存在
if ! jq -e ".[\"$STOCK_CODE\"][\"$MODULE\"]" $CONFIG_FILE > /dev/null 2>&1; then
  jq ".[\"$STOCK_CODE\"][\"$MODULE\"] = {}" $CONFIG_FILE > temp.json && mv temp.json $CONFIG_FILE
fi

# 设置参数值
jq ".[\"$STOCK_CODE\"][\"$MODULE\"][\"$PARAM_NAME\"] = $PARAM_VALUE" $CONFIG_FILE > temp.json && mv temp.json $CONFIG_FILE

echo "已成功设置 $STOCK_CODE 的 $MODULE.$PARAM_NAME 为 $PARAM_VALUE"
```

使用方法：
```bash
chmod +x ~/elephant-strategy/adjust_params.sh
# 例如，调整000001的大象委托量阈值
~/elephant-strategy/adjust_params.sh 000001 大象识别 大象委托量阈值 2000000
```

## 7. 日常维护

### 7.1 查看日志

查看策略运行日志：

```bash
# 查看最近的日志
tail -f ~/elephant-strategy/大象策略/logs/策略运行.log

# 查看特定日期的日志
cat ~/elephant-strategy/大象策略/logs/大象策略_20230101.log
```

### 7.2 备份配置

定期备份你的配置文件是个好习惯：

```bash
# 创建备份目录
mkdir -p ~/elephant-strategy/backups

# 备份配置文件
cp -r ~/elephant-strategy/大象策略/modules/config ~/elephant-strategy/backups/config_$(date +%Y%m%d)
```

### 7.3 停止策略

```bash
# 找到策略运行的进程ID
ps -ef | grep "python 运行测试.py" | grep -v grep

# 停止进程（替换1234为实际的进程ID）
kill 1234
```

## 8. 常见问题解答

### 问题1：启动策略时提示"无法导入模块"

**解决方法**：
```bash
# 确保你在正确的目录下
cd ~/elephant-strategy/大象策略

# 尝试将当前目录添加到Python路径
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 再次启动策略
python 运行测试.py
```

### 问题2：策略无法连接到交易账户

**解决方法**：
1. 检查你的网络连接是否正常
2. 确认交易账户信息是否正确
3. 检查防火墙设置，必要时开放相关端口：
```bash
sudo firewall-cmd --zone=public --add-port=9876/tcp --permanent
sudo firewall-cmd --reload
```

### 问题3：日志显示"CTA引擎未初始化"

**解决方法**：
这通常是因为策略启动时尚未完成初始化。等待几分钟后再检查日志，如果问题持续，尝试重启策略。

### 问题4：品种参数没有生效

**解决方法**：
1. 检查`symbol_params.json`文件格式是否正确（合法的JSON格式）
2. 确保参数名称与全局参数完全一致（包括大小写）
3. 重启策略使新配置生效
4. 检查日志，看是否有加载配置相关的错误信息

### 问题5：如何设置策略自动启动

**解决方法**：
将启动命令添加到系统的自启动服务：
```bash
# 创建服务文件
sudo vim /etc/systemd/system/elephant-strategy.service

# 添加以下内容
[Unit]
Description=大象策略交易服务
After=network.target

[Service]
User=你的用户名
WorkingDirectory=/home/你的用户名/elephant-strategy
ExecStart=/home/你的用户名/elephant-strategy/start_elephant.sh
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target

# 保存并退出后，启用服务
sudo systemctl daemon-reload
sudo systemctl enable elephant-strategy
sudo systemctl start elephant-strategy
```

---

**重要提示**：
1. 实盘交易前，请务必在模拟环境中充分测试你的参数设置
2. 定期检查日志，确保策略正常运行
3. 交易初期使用较小资金，确认策略稳定后再增加资金量
4. 不同股票的特性差别很大，善用品种特定参数可以显著提高策略表现
5. 根据市场变化及时调整参数，市场状态改变时及时调整总体策略
6. 遇到问题时，先查看日志，理解错误信息再采取行动

通过遵循本文档的指导，即使是零基础用户也能成功部署和运行大象策略，并利用品种特定参数针对不同股票进行精细化调整。如有其他问题，请随时咨询技术支持。
