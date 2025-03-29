#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网页管理模块 - 提供远程监控和控制策略的Web接口
"""
from typing import Dict, List, Any, Optional, Union, Callable
import os
import json
import time
import threading
from datetime import datetime, timezone, timedelta
import socket
import logging
from functools import wraps
import webbrowser

# Flask相关导入
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("网页管理")

# 可配置参数
默认设置 = {
    "端口": 8088,
    "主机": "0.0.0.0",
    "自动打开浏览器": True,
    "刷新间隔": 3,
    "日志保留天数": 30,
    "最大连接数": 10,
    "认证有效期": 24,
    "允许远程访问": False,
    "日志级别": "INFO"
}

class 网页管理器:
    """
    网页管理器类，提供远程监控和控制策略的Web接口
    """
    
    class User(UserMixin):
        """用户类，用于Flask-Login认证"""
        def __init__(self, id):
            self.id = id
            
        def get_id(self):
            return self.id
    
    def __init__(
        self, 
        端口: int = 8888, 
        主机: str = "127.0.0.1", 
        自动打开浏览器: bool = True,
        参数管理器 = None,
        用户名: str = "admin",
        密码: str = "admin"
    ):
        """
        初始化网页管理器
        
        参数:
            端口: 网页服务端口号
            主机: 网页服务主机地址
            自动打开浏览器: 是否自动打开浏览器
            参数管理器: 参数管理器实例
            用户名: 登录用户名，默认admin
            密码: 登录密码，默认admin
        """
        self.端口 = 端口
        self.主机 = 主机
        self.自动打开浏览器 = 自动打开浏览器
        
        # 存储参数管理器
        self.参数管理器 = 参数管理器
        
        # 认证相关
        self.认证需要 = True  # 启用认证
        self.认证用户名 = 用户名
        self.认证密码_哈希 = generate_password_hash(密码) if 密码 else None
        self.认证有效期 = 24  # 认证有效期(小时)
        
        # 其他变量
        self.策略 = None
        self.线程 = None
        self.运行中 = False
        self.最新价格 = {}
        self.持仓信息 = {}
        self.账户信息 = {}
        self.交易记录 = []
        self.大象记录 = {}
        self.最近风控事件 = []
        self.刷新间隔 = 2  # 页面自动刷新间隔(秒)
        
        # 服务器相关
        self.服务器线程 = None
        
        # 数据存储
        self.日志 = []
        self.最大日志数量 = 500
        self.大象数据 = {}
        self.策略状态 = {
            "运行状态": "未连接",
            "启动时间": "",
            "运行时长": "",
            "已识别大象": 0,
            "活跃订单数": 0,
            "今日交易次数": 0,
            "今日盈亏": 0.0,
            "总盈亏": 0.0
        }
        
        # 静态路径
        self.静态文件路径 = os.path.join(os.path.dirname(__file__), "static")
        self.模板路径 = os.path.join(os.path.dirname(__file__), "templates")
        
        # 确保目录存在
        os.makedirs(self.静态文件路径, exist_ok=True)
        os.makedirs(self.模板路径, exist_ok=True)
        
        # 初始化应用
        self._初始化应用()
    
    def _初始化应用(self):
        """初始化Flask应用"""
        self.app = Flask(__name__, 
                         static_folder=self.静态文件路径, 
                         template_folder=self.模板路径)
        self.app.secret_key = os.urandom(24)
        self.app.config['PERMANENT_SESSION_LIFETIME'] = self.认证有效期 * 3600
        
        # 初始化登录管理器
        login_manager = LoginManager()
        login_manager.init_app(self.app)
        login_manager.login_view = 'login'
        
        @login_manager.user_loader
        def load_user(user_id):
            if user_id == self.认证用户名:
                return self.User(user_id)
            return None
        
        # 注册路由
        self._注册路由()
        
        # 移除SocketIO初始化，改为使用轮询机制
    
    def _注册路由(self):
        """注册Flask路由"""
        app = self.app
        
        @app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                
                if username == self.认证用户名 and (not self.认证密码_哈希 or check_password_hash(self.认证密码_哈希, password)):
                    user = self.User(username)  # 现在使用类成员变量User
                    login_user(user, remember=True)
                    next_page = request.args.get('next', '/')
                    return redirect(next_page)
                
                return render_template('login.html', error='无效的用户名或密码')
            
            return render_template('login.html')
        
        @app.route('/logout')
        @login_required
        def logout():
            logout_user()
            return redirect(url_for('login'))
        
        @app.route('/')
        @login_required
        def index():
            if self.认证需要 and not current_user.is_authenticated:
                return redirect(url_for('login'))
            return render_template('index.html', 刷新间隔=self.刷新间隔, 策略状态=self.策略状态, 大象数据=self.大象数据)
        
        @app.route('/monitor')
        @login_required
        def monitor():
            if self.认证需要 and not current_user.is_authenticated:
                return redirect(url_for('login'))
            return render_template('monitor.html', 刷新间隔=self.刷新间隔, 策略状态=self.策略状态, 大象数据=self.大象数据)
        
        @app.route('/stats')
        @login_required
        def stats():
            return render_template('stats.html', 
                                    策略状态=self.策略状态,
                                    大象数据=self.大象数据,
                                    刷新间隔=self.刷新间隔)
        
        @app.route('/trades')
        @login_required
        def trades():
            return render_template('trades.html',
                                    交易记录=self.交易记录,
                                    刷新间隔=self.刷新间隔)
        
        @app.route('/settings', methods=['GET'])
        @login_required
        def settings():
            if self.认证需要 and not current_user.is_authenticated:
                return redirect(url_for('login'))
            
            # 获取当前策略参数，但不允许修改
            参数 = self.策略.get_parameters() if self.策略 else {}
            return render_template('settings.html', 参数=参数, 刷新间隔=self.刷新间隔, 只读模式=True)
        
        @app.route('/symbol_params', methods=['GET'])
        def symbol_params():
            if self.认证需要 and not current_user.is_authenticated:
                return redirect(url_for('login'))
            
            # 获取所有交易品种
            股票列表 = []
            if self.参数管理器:
                股票列表 = self.参数管理器.获取股票列表()
                self.记录日志(f"获取股票列表: {股票列表}")
            elif self.策略:
                股票列表 = self.策略.交易股票列表 if hasattr(self.策略, '交易股票列表') else []
            
            # 获取全局参数
            全局参数 = {}
            if self.参数管理器:
                全局参数 = self.参数管理器.全局参数
                self.记录日志(f"获取全局参数: {全局参数}")
            
            # 确保全局参数包含所有必要的模块
            if not 全局参数 or not isinstance(全局参数, dict):
                全局参数 = {}
            
            if "大象识别" not in 全局参数:
                全局参数["大象识别"] = {}
            if "交易执行" not in 全局参数:
                全局参数["交易执行"] = {}
            if "风险控制" not in 全局参数:
                全局参数["风险控制"] = {}
            if "资金管理" not in 全局参数:
                全局参数["资金管理"] = {}
            
            # 确保价差阈值参数为整数类型
            if "大象价差阈值" in 全局参数["大象识别"]:
                全局参数["大象识别"]["大象价差阈值"] = int(全局参数["大象识别"]["大象价差阈值"])
            if "卖单价差阈值" in 全局参数["大象识别"]:
                全局参数["大象识别"]["卖单价差阈值"] = int(全局参数["大象识别"]["卖单价差阈值"])
            
            # 添加提示信息，说明参数只能通过配置文件设置
            提示信息 = "参数设置已移至配置文件，请直接修改配置文件进行参数设置。网页界面仅供查看参数信息。"
            
            return render_template('symbol_params.html', 
                                  股票列表=股票列表, 
                                  全局参数=全局参数,
                                  刷新间隔=self.刷新间隔,
                                  提示信息=提示信息,
                                  只读模式=True)
        
        @app.route('/get_symbol_params/<symbol>', methods=['GET'])
        def get_symbol_params(symbol):
            if self.认证需要 and not current_user.is_authenticated:
                return jsonify({"error": "需要登录"}), 401
            
            if not self.参数管理器:
                self.记录日志(f"错误: 参数管理器未初始化")
                return jsonify({"error": "参数管理器未初始化"}), 500
            
            try:
                # 确认股票代码存在
                股票列表 = self.参数管理器.获取股票列表()
                self.记录日志(f"获取股票列表结果: {股票列表}")
                
                if symbol not in 股票列表:
                    self.记录日志(f"错误: 股票代码 {symbol} 不在交易列表中")
                    return jsonify({"error": f"股票代码 {symbol} 不在交易列表中"}), 404
                
                # 获取品种特定参数
                self.记录日志(f"开始获取品种参数: {symbol}")
                品种参数 = self.参数管理器.获取品种所有参数(symbol)
                
                # 确保价差阈值参数为整数类型
                if "大象识别" in 品种参数:
                    if "大象价差阈值" in 品种参数["大象识别"]:
                        品种参数["大象识别"]["大象价差阈值"] = int(品种参数["大象识别"]["大象价差阈值"])
                    if "卖单价差阈值" in 品种参数["大象识别"]:
                        品种参数["大象识别"]["卖单价差阈值"] = int(品种参数["大象识别"]["卖单价差阈值"])
                
                # 记录日志
                self.记录日志(f"获取品种参数成功: {symbol}, 参数: {品种参数}")
                
                # 确保返回的是合法的JSON格式
                if not 品种参数:
                    # 如果没有参数，返回默认结构
                    return jsonify({
                        "大象识别": {},
                        "交易执行": {},
                        "风险控制": {},
                        "资金管理": {}
                    })
                
                return jsonify(品种参数)
            except Exception as e:
                self.记录日志(f"获取品种参数出错: {symbol}, 错误: {str(e)}")
                import traceback
                self.记录日志(f"错误详情: {traceback.format_exc()}")
                return jsonify({"error": f"获取品种参数出错: {str(e)}"}), 500
        
        @app.route('/add_stock', methods=['POST'])
        def add_stock():
            if self.认证需要 and not current_user.is_authenticated:
                return jsonify({"error": "需要登录"})
            
            股票代码 = request.form.get('stock_code')
            if not 股票代码 or not (股票代码.isdigit() and len(股票代码) == 6):
                return jsonify({"error": "无效的股票代码"})
            
            # 优先使用参数管理器
            if self.参数管理器:
                当前股票列表 = self.参数管理器.获取股票列表()
                if 股票代码 not in 当前股票列表:
                    当前股票列表.append(股票代码)
                    self.参数管理器.设置股票列表(当前股票列表)
                    self.记录日志(f"添加交易股票: {股票代码}")
                    
                    # 如果策略也存在，同步更新策略的股票列表
                    if self.策略 and hasattr(self.策略, '交易股票列表'):
                        if 股票代码 not in self.策略.交易股票列表:
                            self.策略.交易股票列表.append(股票代码)
                            if hasattr(self.策略, '_订阅股票行情') and callable(self.策略._订阅股票行情):
                                self.策略._订阅股票行情()
                    
                    return jsonify({"success": True})
                else:
                    return jsonify({"error": "股票已在交易列表中"})
            
            # 如果没有参数管理器，则使用策略
            elif self.策略 and hasattr(self.策略, '交易股票列表'):
                if 股票代码 not in self.策略.交易股票列表:
                    self.策略.交易股票列表.append(股票代码)
                    if hasattr(self.策略, '_订阅股票行情') and callable(self.策略._订阅股票行情):
                        self.策略._订阅股票行情()
                    self.记录日志(f"添加交易股票: {股票代码}")
                    return jsonify({"success": True})
                else:
                    return jsonify({"error": "股票已在交易列表中"})
            else:
                return jsonify({"error": "系统未初始化"})
        
        @app.route('/remove_stock/<symbol>', methods=['POST'])
        def remove_stock(symbol):
            if self.认证需要 and not current_user.is_authenticated:
                return jsonify({"error": "需要登录"})
            
            # 优先使用参数管理器
            if self.参数管理器:
                当前股票列表 = self.参数管理器.获取股票列表()
                if symbol in 当前股票列表:
                    当前股票列表.remove(symbol)
                    self.参数管理器.设置股票列表(当前股票列表)
                    self.记录日志(f"删除交易股票: {symbol}")
                    
                    # 如果策略也存在，同步更新策略的股票列表
                    if self.策略 and hasattr(self.策略, '交易股票列表'):
                        if symbol in self.策略.交易股票列表:
                            self.策略.交易股票列表.remove(symbol)
                    
                    return jsonify({"success": True})
                else:
                    return jsonify({"error": "股票不在交易列表中"})
            
            # 如果没有参数管理器，则使用策略
            elif self.策略 and hasattr(self.策略, '交易股票列表'):
                if symbol in self.策略.交易股票列表:
                    self.策略.交易股票列表.remove(symbol)
                    self.记录日志(f"删除交易股票: {symbol}")
                    return jsonify({"success": True})
                else:
                    return jsonify({"error": "股票不在交易列表中"})
            else:
                return jsonify({"error": "系统未初始化"})
        
        @app.route('/logs')
        @login_required
        def logs():
            if self.认证需要 and not current_user.is_authenticated:
                return redirect(url_for('login'))
            return render_template('logs.html', 刷新间隔=self.刷新间隔)
        
        @app.route('/api/status')
        @login_required
        def api_status():
            return jsonify(self.策略状态)
        
        @app.route('/api/elephants')
        @login_required
        def api_elephants():
            elephant_type = request.args.get('type', 'all')
            status = request.args.get('status', 'active')
            
            大象列表 = []
            for code, data in self.大象数据.items():
                for elephant in data:
                    # 根据类型和状态筛选
                    if (elephant_type == 'all' or 
                        (elephant_type == 'upper' and elephant['类型'] == '上方大象') or
                        (elephant_type == 'lower' and elephant['类型'] == '下方大象')):
                        if (status == 'all' or 
                            (status == 'active' and elephant['状态'] == '活跃')):
                            大象列表.append(elephant)
            
            return jsonify({"大象列表": 大象列表})
        
        @app.route('/api/trades')
        @login_required
        def api_trades():
            date = request.args.get('date')
            stock = request.args.get('stock')
            trade_type = request.args.get('type')
            
            filteredTrades = self.交易记录
            
            # 应用过滤器
            if date:
                if date == 'today':
                    today = datetime.now().strftime('%Y-%m-%d')
                    filteredTrades = [t for t in filteredTrades if t['交易时间'].startswith(today)]
                else:
                    filteredTrades = [t for t in filteredTrades if t['交易时间'].startswith(date)]
            
            if stock:
                filteredTrades = [t for t in filteredTrades if t['股票代码'] == stock]
            
            if trade_type:
                filteredTrades = [t for t in filteredTrades if t['交易类型'] == trade_type]
            
            return jsonify({"交易记录": filteredTrades})
        
        @app.route('/api/assets')
        @login_required
        def api_assets():
            if not self.策略:
                return jsonify({"error": "策略未连接"})
            
            资产数据 = self.策略.get_assets() if hasattr(self.策略, 'get_assets') else {}
            return jsonify(资产数据)
        
        @app.route('/api/control', methods=['POST'])
        @login_required
        def api_control():
            action = request.form.get('action')
            
            if not self.策略:
                return jsonify({"success": False, "message": "策略未连接"})
            
            if action == 'start':
                if hasattr(self.策略, 'start_trading') and callable(self.策略.start_trading):
                    self.策略.start_trading()
                    self.记录日志("通过Web界面启动策略")
                    return jsonify({"success": True, "message": "策略已启动"})
            
            elif action == 'stop':
                if hasattr(self.策略, 'stop_trading') and callable(self.策略.stop_trading):
                    self.策略.stop_trading()
                    self.记录日志("通过Web界面停止策略")
                    return jsonify({"success": True, "message": "策略已停止"})
            
            elif action == 'pause':
                if hasattr(self.策略, 'pause_trading') and callable(self.策略.pause_trading):
                    self.策略.pause_trading()
                    self.记录日志("通过Web界面暂停策略")
                    return jsonify({"success": True, "message": "策略已暂停"})
            
            elif action == 'resume':
                if hasattr(self.策略, 'resume_trading') and callable(self.策略.resume_trading):
                    self.策略.resume_trading()
                    self.记录日志("通过Web界面恢复策略")
                    return jsonify({"success": True, "message": "策略已恢复"})
            
            return jsonify({"success": False, "message": f"不支持的操作: {action}"})
        
        @app.route('/api/logs')
        def api_logs():
            if self.认证需要 and not current_user.is_authenticated:
                return jsonify([])
            return jsonify(self.日志)
        
        @app.route('/api/latest_logs')
        @login_required
        def api_latest_logs():
            """获取最新的日志，用于轮询"""
            count = request.args.get('count', 10, type=int)
            return jsonify({"日志": self.日志[-count:] if len(self.日志) > 0 else []})
    
    # 移除WebSocket事件处理函数，改为使用API端点实现轮询
    
    def 连接策略(self, 策略实例):
        """
        连接到策略实例
        
        参数:
            策略实例: 大象策略实例
        """
        self.策略 = 策略实例
        self.记录日志("网页管理器已连接到策略实例")
        
        # 如果策略已经有状态信息，更新本地状态
        if hasattr(策略实例, 'get_status') and callable(策略实例.get_status):
            status = 策略实例.get_status()
            if status:
                self.更新状态(status)
    
    def 启动(self):
        """启动Web服务器"""
        if self.运行中:
            return
        
        try:
            # 在单独的线程中启动服务器
            self.服务器线程 = threading.Thread(target=self._运行服务器)
            self.服务器线程.daemon = True
            self.服务器线程.start()
            
            self.运行中 = True
            self.记录日志(f"网页管理服务已启动，地址: http://{self.主机}:{self.端口}")
            
            # 自动打开浏览器
            if self.自动打开浏览器:
                webbrowser.open(f"http://localhost:{self.端口}")
                
            return True
        except Exception as e:
            self.记录日志(f"启动Web服务器错误: {e}")
            logger.exception("启动Web服务器错误")
            return False
    
    def 停止(self):
        """停止Web服务器"""
        if not self.运行中:
            return
        
        try:
            # 关闭服务器
            self.运行中 = False
            self.记录日志("网页管理服务已停止")
            return True
        except Exception as e:
            self.记录日志(f"停止Web服务器错误: {e}")
            logger.exception("停止Web服务器错误")
            return False
    
    def _运行服务器(self):
        """在线程中运行Flask服务器"""
        try:
            # 添加服务器启动信息
            print(f"正在启动服务器，访问地址: http://{self.主机 if self.主机 != '0.0.0.0' else 'localhost'}:{self.端口}")
            # 使用普通的Flask run方法运行服务器
            self.app.run(
                host=self.主机, 
                port=self.端口, 
                debug=False, 
                use_reloader=False,     # 关闭重载器以避免双重启动
                threaded=True          # 使用线程模式
            )
        except Exception as e:
            self.记录日志(f"运行Web服务器错误: {e}")
            logger.exception("运行Web服务器错误")
            self.运行中 = False
    
    def 记录日志(self, 消息):
        """
        记录日志消息
        
        参数:
            消息: 日志消息
        """
        时间 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        日志条目 = {"时间": 时间, "消息": 消息}
        
        # 添加到日志列表
        self.日志.append(日志条目)
        
        # 超出最大数量时，删除旧的日志
        if len(self.日志) > self.最大日志数量:
            self.日志 = self.日志[-self.最大日志数量:]
        
        # 记录到系统日志
        logger.info(消息)
    
    def 更新状态(self, 状态数据):
        """
        更新策略状态
        
        参数:
            状态数据: 策略状态数据字典
        """
        # 更新状态字典
        self.策略状态.update(状态数据)
    
    def 更新大象数据(self, 股票代码, 大象数据):
        """
        更新大象数据
        
        参数:
            股票代码: 股票代码
            大象数据: 大象数据列表
        """
        self.大象数据[股票代码] = 大象数据
    
    def 更新交易记录(self, 交易记录):
        """
        更新交易记录
        
        参数:
            交易记录: 交易记录字典或列表
        """
        if isinstance(交易记录, dict):
            self.交易记录.append(交易记录)
        elif isinstance(交易记录, list):
            self.交易记录.extend(交易记录)
    
    def _创建基础模板文件(self):
        """创建基础模板文件"""
        # 这里应该创建必要的HTML模板文件，但为了简化代码，这里省略具体实现
        pass


# 创建默认的模板文件
def 创建默认模板文件(目录):
    """创建默认的HTML模板文件"""
    # 这里应该创建必要的HTML模板文件，但为了简化代码，这里省略具体实现
    pass


# 运行测试服务器
if __name__ == "__main__":
    # 导入参数管理器
    from 参数管理 import 参数管理器
    
    # 打印当前工作目录
    import os
    当前目录 = os.path.dirname(os.path.abspath(__file__))
    print(f"当前工作目录: {当前目录}")
    
    # 确保配置目录存在
    配置目录 = os.path.join(当前目录, "config")
    os.makedirs(配置目录, exist_ok=True)
    print(f"配置目录: {配置目录}")
    
    # 创建参数管理器实例
    参数管理实例 = 参数管理器(配置目录=配置目录)
    
    # 初始化默认参数
    默认参数 = {
        "全局参数": {
            "大象识别": {
                "大象委托量阈值": 5000000,
                "大象价差阈值": 3,
                "大象确认次数": 3,
                "大象稳定时间": 5,
                "启用卖单识别": True,
                "卖单委托量阈值": 5000000,
                "卖单价差阈值": 3,
                "跳过买一价": True,
                "远距大象委托量倍数": 2
            },
            "交易执行": {
                "价格偏移量": 0.01,
                "等待时间": 10,
                "冷却时间": 60,
                "调戏交易量": 100
            },
            "风险控制": {
                "单笔最大亏损比例": 0.01,
                "单股最大亏损比例": 0.02,
                "单股最大交易次数": 10,
                "总交易次数限制": 30
            },
            "资金管理": {
                "单股最大仓位比例": 0.1
            }
        }
    }
    参数管理实例.初始化默认参数(默认参数)
    
    # 创建网页管理器实例
    管理器 = 网页管理器(端口=8088, 主机="127.0.0.1", 自动打开浏览器=True, 参数管理器=参数管理实例)
    
    # 模拟股票列表
    股票列表 = ["000001", "600000", "600036"]
    参数管理实例.设置股票列表(股票列表)
    
    # 启动服务器
    管理器.启动()
    
    # 模拟更新数据
    def 模拟数据更新():
        import random
        
        while 管理器.运行中:
            # 更新状态
            管理器.更新状态({
                "运行状态": "正常",
                "已识别大象": random.randint(1, 10),
                "活跃订单数": random.randint(0, 5),
                "今日交易次数": random.randint(10, 30),
                "今日盈亏": random.randint(-5000, 10000) / 100
            })
            
            # 记录日志
            管理器.记录日志(f"模拟日志消息: {datetime.now()}")
            
            # 等待一段时间
            time.sleep(5)
    
    # 启动模拟数据更新线程
    数据线程 = threading.Thread(target=模拟数据更新)
    数据线程.daemon = True
    数据线程.start()
    
    print("网页管理服务已启动，访问 http://127.0.0.1:8088 打开管理界面")
    
    # 保持程序运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("退出程序")