#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网页管理模块 - 提供远程监控和控制策略的Web接口
"""
from typing import Dict, List, Any, Optional, Callable
import os
import json
import time
import threading
from datetime import datetime
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import urllib.parse

# 基础HTML模板
HTML_模板 = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>大象策略 - 远程管理</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { width: 90%; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background-color: #333; color: white; padding: 15px 0; text-align: center; }
        .nav { background-color: #444; overflow: hidden; }
        .nav a { float: left; display: block; color: white; text-align: center; padding: 14px 16px; text-decoration: none; }
        .nav a:hover { background-color: #555; }
        .nav a.active { background-color: #4CAF50; }
        .section { background-color: white; margin: 20px 0; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .footer { background-color: #333; color: white; text-align: center; padding: 10px 0; position: fixed; bottom: 0; width: 100%; }
        table { width: 100%; border-collapse: collapse; }
        table, th, td { border: 1px solid #ddd; }
        th, td { padding: 12px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .btn { display: inline-block; padding: 8px 16px; margin: 5px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background-color: #45a049; }
        .btn-danger { background-color: #f44336; }
        .btn-danger:hover { background-color: #d32f2f; }
        .btn-warning { background-color: #ff9800; }
        .btn-warning:hover { background-color: #e68a00; }
        .status-good { color: green; }
        .status-warning { color: orange; }
        .status-bad { color: red; }
        .refresh { margin-top: 20px; text-align: right; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input[type="text"], input[type="number"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
    </style>
    <script>
        function refreshPage() {
            location.reload();
        }
        
        function sendCommand(cmd, params) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/command';
            
            // 添加命令
            const cmdField = document.createElement('input');
            cmdField.type = 'hidden';
            cmdField.name = 'cmd';
            cmdField.value = cmd;
            form.appendChild(cmdField);
            
            // 添加参数
            if (params) {
                for (const key in params) {
                    const paramField = document.createElement('input');
                    paramField.type = 'hidden';
                    paramField.name = key;
                    paramField.value = params[key];
                    form.appendChild(paramField);
                }
            }
            
            document.body.appendChild(form);
            form.submit();
        }
        
        // 自动刷新
        setTimeout(refreshPage, 30000); // 30秒刷新一次
    </script>
</head>
<body>
    <div class="header">
        <h1>大象策略 - 远程管理系统</h1>
    </div>
    <div class="nav">
        <a href="/" class="active">首页</a>
        <a href="/stats">策略统计</a>
        <a href="/trades">交易记录</a>
        <a href="/settings">参数设置</a>
        <a href="/logs">运行日志</a>
    </div>
    <div class="container">
        {内容}
    </div>
    <div class="footer">
        <p>大象策略 &copy; {年份} - 运行状态: {运行状态}</p>
    </div>
</body>
</html>
"""


class 网页管理器:
    """网页管理器类，提供远程管理接口"""
    
    def __init__(
        self, 
        端口: int = 8088,
        自动打开浏览器: bool = True,
        主机: str = "localhost"
    ):
        """
        初始化网页管理器
        
        参数:
            端口: Web服务器端口号
            自动打开浏览器: 是否自动打开浏览器
            主机: 服务器主机名
        """
        self.端口 = 端口
        self.主机 = 主机
        self.自动打开浏览器 = 自动打开浏览器
        self.服务器 = None
        self.服务器线程 = None
        self.运行中 = False
        
        # 策略引用
        self.策略 = None
        
        # 页面处理函数
        self.页面处理器 = {
            "/": self._首页,
            "/stats": self._统计页面,
            "/trades": self._交易记录页面,
            "/settings": self._参数设置页面,
            "/logs": self._日志页面
        }
        
        # 命令处理函数
        self.命令处理器 = {
            "start": self._开始策略,
            "stop": self._停止策略,
            "update_settings": self._更新参数
        }
        
        # 日志记录
        self.日志 = []
        self.最大日志数量 = 200
    
    def 连接策略(self, 策略实例):
        """
        连接到策略实例
        
        参数:
            策略实例: 大象策略实例
        """
        self.策略 = 策略实例
        self.记录日志("网页管理器已连接到策略实例")
    
    def 启动(self):
        """启动Web服务器"""
        if self.运行中:
            return
        
        try:
            管理器 = self  # 为了在请求处理器中访问管理器
            
            class 请求处理器(BaseHTTPRequestHandler):
                """HTTP请求处理器"""
                
                def do_GET(self):
                    """处理GET请求"""
                    路径 = urllib.parse.urlparse(self.path).path
                    
                    # 如果路径对应某个页面处理器，使用该处理器
                    if 路径 in 管理器.页面处理器:
                        内容 = 管理器.页面处理器[路径]()
                        self._发送响应(200, 内容)
                    else:
                        self._发送响应(404, "页面未找到")
                
                def do_POST(self):
                    """处理POST请求"""
                    路径 = urllib.parse.urlparse(self.path).path
                    
                    if 路径 == "/command":
                        # 处理命令
                        内容长度 = int(self.headers['Content-Length'])
                        请求数据 = self.rfile.read(内容长度).decode('utf-8')
                        参数 = urllib.parse.parse_qs(请求数据)
                        
                        命令 = 参数.get('cmd', [''])[0]
                        
                        if 命令 in 管理器.命令处理器:
                            结果 = 管理器.命令处理器[命令](参数)
                            self._发送响应(200, f"<script>alert('{结果}'); window.location='/';</script>")
                        else:
                            self._发送响应(400, f"<script>alert('未知命令: {命令}'); window.location='/';</script>")
                    else:
                        self._发送响应(404, "接口未找到")
                
                def _发送响应(self, 状态码, 内容):
                    """发送HTTP响应"""
                    self.send_response(状态码)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    
                    完整内容 = HTML_模板.format(
                        内容=内容,
                        年份=datetime.now().year,
                        运行状态="正在运行" if 管理器.策略 and 管理器.策略.trading else "已停止"
                    )
                    
                    self.wfile.write(完整内容.encode('utf-8'))
                
                def log_message(self, format, *args):
                    """重写日志方法，避免控制台输出"""
                    管理器.记录日志(f"HTTP {args[0]} {args[1]} {args[2]}")
            
            # 创建HTTP服务器
            self.服务器 = HTTPServer((self.主机, self.端口), 请求处理器)
            
            # 在单独的线程中启动服务器
            self.服务器线程 = threading.Thread(target=self._运行服务器)
            self.服务器线程.daemon = True
            self.服务器线程.start()
            
            self.运行中 = True
            self.记录日志(f"网页管理服务已启动，地址: http://{self.主机}:{self.端口}")
            
            # 自动打开浏览器
            if self.自动打开浏览器:
                webbrowser.open(f"http://{self.主机}:{self.端口}")
                
            return True
        except Exception as e:
            self.记录日志(f"启动Web服务器错误: {e}")
            return False
    
    def 停止(self):
        """停止Web服务器"""
        if not self.运行中:
            return
        
        try:
            self.服务器.shutdown()
            self.服务器.server_close()
            self.服务器线程.join(1)
            self.运行中 = False
            self.记录日志("网页管理服务已停止")
            return True
        except Exception as e:
            self.记录日志(f"停止Web服务器错误: {e}")
            return False
    
    def 记录日志(self, 消息: str):
        """
        记录日志消息
        
        参数:
            消息: 日志消息
        """
        日志项 = {
            "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "消息": 消息
        }
        
        self.日志.append(日志项)
        
        # 限制日志数量
        if len(self.日志) > self.最大日志数量:
            self.日志 = self.日志[-self.最大日志数量:]
    
    def _运行服务器(self):
        """在线程中运行HTTP服务器"""
        try:
            self.服务器.serve_forever()
        except Exception as e:
            self.记录日志(f"服务器运行错误: {e}")
    
    # 页面生成函数
    def _首页(self) -> str:
        """生成首页内容"""
        if not self.策略:
            return """
                <div class="section">
                    <h2>未连接策略</h2>
                    <p>网页管理器尚未连接到策略实例。</p>
                </div>
            """
        
        # 获取策略状态
        状态 = "运行中" if self.策略.trading else "已停止"
        状态类 = "status-good" if self.策略.trading else "status-warning"
        
        # 获取最近交易
        最近交易 = []
        if hasattr(self.策略, "交易执行器") and self.策略.交易执行器:
            最近交易 = self.策略.交易执行器.完成订单[-5:] if self.策略.交易执行器.完成订单 else []
        
        # 构建首页内容
        内容 = f"""
            <div class="section">
                <h2>策略状态</h2>
                <p>当前状态：<span class="{状态类}">{状态}</span></p>
                <div>
                    <button class="btn" onclick="sendCommand('start')">启动策略</button>
                    <button class="btn btn-danger" onclick="sendCommand('stop')">停止策略</button>
                </div>
            </div>
            
            <div class="section">
                <h2>策略概览</h2>
                <table>
                    <tr>
                        <th>策略名称</th>
                        <td>大象策略</td>
                    </tr>
                    <tr>
                        <th>启动时间</th>
                        <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                    <tr>
                        <th>交易股票数量</th>
                        <td>{len(self.策略.交易股票列表)}</td>
                    </tr>
                </table>
            </div>
            
            <div class="section">
                <h2>最近交易</h2>
        """
        
        if 最近交易:
            内容 += """
                <table>
                    <tr>
                        <th>订单ID</th>
                        <th>股票代码</th>
                        <th>方向</th>
                        <th>价格</th>
                        <th>数量</th>
                        <th>状态</th>
                    </tr>
            """
            
            for 订单 in reversed(最近交易):
                内容 += f"""
                    <tr>
                        <td>{订单.get("订单ID", "")}</td>
                        <td>{订单.get("股票代码", "")}</td>
                        <td>{订单.get("方向", "")}</td>
                        <td>{订单.get("价格", "")}</td>
                        <td>{订单.get("数量", "")}</td>
                        <td>{订单.get("状态", "")}</td>
                    </tr>
                """
            
            内容 += "</table>"
        else:
            内容 += "<p>暂无交易记录</p>"
        
        内容 += """
            </div>
            
            <div class="refresh">
                <button class="btn" onclick="refreshPage()">刷新页面</button>
            </div>
        """
        
        return 内容
    
    def _统计页面(self) -> str:
        """生成统计页面内容"""
        if not self.策略:
            return "<div class='section'><h2>未连接策略</h2><p>网页管理器尚未连接到策略实例。</p></div>"
        
        内容 = """
            <div class="section">
                <h2>策略统计</h2>
        """
        
        # 资金统计
        资金统计 = {}
        if hasattr(self.策略, "资金管理器") and self.策略.资金管理器:
            资金统计 = self.策略.资金管理器.获取每日统计()
            
            内容 += """
                <h3>资金统计</h3>
                <table>
                    <tr>
                        <th>项目</th>
                        <th>金额</th>
                    </tr>
            """
            
            for 键, 值 in 资金统计.items():
                内容 += f"""
                    <tr>
                        <td>{键}</td>
                        <td>{值}</td>
                    </tr>
                """
            
            内容 += "</table>"
        else:
            内容 += "<p>暂无资金统计数据</p>"
        
        # 风控统计
        风控统计 = {}
        if hasattr(self.策略, "风险控制器") and self.策略.风险控制器:
            风控统计 = self.策略.风险控制器.获取风控状态()
            
            内容 += """
                <h3>风控统计</h3>
                <table>
                    <tr>
                        <th>项目</th>
                        <th>数值</th>
                    </tr>
            """
            
            for 键, 值 in 风控统计.items():
                if 键 != "单股交易次数" and 键 != "单股盈亏" and 键 != "上次重置时间":
                    内容 += f"""
                        <tr>
                            <td>{键}</td>
                            <td>{值}</td>
                        </tr>
                    """
            
            内容 += "</table>"
            
            # 单股统计
            内容 += """
                <h3>单股统计</h3>
                <table>
                    <tr>
                        <th>股票代码</th>
                        <th>交易次数</th>
                        <th>盈亏</th>
                    </tr>
            """
            
            单股交易次数 = 风控统计.get("单股交易次数", {})
            单股盈亏 = 风控统计.get("单股盈亏", {})
            
            for 股票代码 in set(list(单股交易次数.keys()) + list(单股盈亏.keys())):
                交易次数 = 单股交易次数.get(股票代码, 0)
                盈亏 = 单股盈亏.get(股票代码, 0)
                
                内容 += f"""
                    <tr>
                        <td>{股票代码}</td>
                        <td>{交易次数}</td>
                        <td>{盈亏}</td>
                    </tr>
                """
            
            内容 += "</table>"
        else:
            内容 += "<p>暂无风控统计数据</p>"
        
        内容 += """
            </div>
            
            <div class="refresh">
                <button class="btn" onclick="refreshPage()">刷新页面</button>
            </div>
        """
        
        return 内容
    
    def _交易记录页面(self) -> str:
        """生成交易记录页面内容"""
        if not self.策略:
            return "<div class='section'><h2>未连接策略</h2><p>网页管理器尚未连接到策略实例。</p></div>"
        
        内容 = """
            <div class="section">
                <h2>交易记录</h2>
        """
        
        # 完成订单
        完成订单 = []
        if hasattr(self.策略, "交易执行器") and self.策略.交易执行器:
            完成订单 = self.策略.交易执行器.完成订单
            
            内容 += """
                <table>
                    <tr>
                        <th>订单ID</th>
                        <th>股票代码</th>
                        <th>方向</th>
                        <th>价格</th>
                        <th>数量</th>
                        <th>状态</th>
                        <th>提交时间</th>
                    </tr>
            """
            
            for 订单 in reversed(完成订单):
                提交时间 = 订单.get("提交时间", "")
                if 提交时间 and isinstance(提交时间, datetime):
                    提交时间 = 提交时间.strftime("%Y-%m-%d %H:%M:%S")
                
                内容 += f"""
                    <tr>
                        <td>{订单.get("订单ID", "")}</td>
                        <td>{订单.get("股票代码", "")}</td>
                        <td>{订单.get("方向", "")}</td>
                        <td>{订单.get("价格", "")}</td>
                        <td>{订单.get("数量", "")}</td>
                        <td>{订单.get("状态", "")}</td>
                        <td>{提交时间}</td>
                    </tr>
                """
            
            内容 += "</table>"
        else:
            内容 += "<p>暂无交易记录</p>"
        
        内容 += """
            </div>
            
            <div class="refresh">
                <button class="btn" onclick="refreshPage()">刷新页面</button>
            </div>
        """
        
        return 内容
    
    def _参数设置页面(self) -> str:
        """生成参数设置页面内容"""
        if not self.策略:
            return "<div class='section'><h2>未连接策略</h2><p>网页管理器尚未连接到策略实例。</p></div>"
        
        内容 = """
            <div class="section">
                <h2>参数设置</h2>
                <form id="settings-form" method="post" action="/command">
                    <input type="hidden" name="cmd" value="update_settings">
                    
                    <h3>大象识别参数</h3>
                    <div class="form-group">
                        <label for="大象委托量阈值">大象委托量阈值</label>
                        <input type="number" id="大象委托量阈值" name="大象委托量阈值" value="{}" step="1000">
                    </div>
                    <div class="form-group">
                        <label for="大象价差阈值">大象价差阈值 (%)</label>
                        <input type="number" id="大象价差阈值" name="大象价差阈值" value="{}" step="0.01">
                    </div>
                    <div class="form-group">
                        <label for="大象确认次数">大象确认次数</label>
                        <input type="number" id="大象确认次数" name="大象确认次数" value="{}" step="1">
                    </div>
                    
                    <h3>交易执行参数</h3>
                    <div class="form-group">
                        <label for="价格偏移量">价格偏移量</label>
                        <input type="number" id="价格偏移量" name="价格偏移量" value="{}" step="0.01">
                    </div>
                    <div class="form-group">
                        <label for="卖出偏移量倍数">卖出偏移量倍数</label>
                        <input type="number" id="卖出偏移量倍数" name="卖出偏移量倍数" value="{}" step="0.1">
                    </div>
                    <div class="form-group">
                        <label for="买入偏移量倍数">买入偏移量倍数</label>
                        <input type="number" id="买入偏移量倍数" name="买入偏移量倍数" value="{}" step="0.1">
                    </div>
                    
                    <h3>资金管理参数</h3>
                    <div class="form-group">
                        <label for="股票池比例">股票池比例</label>
                        <input type="number" id="股票池比例" name="股票池比例" value="{}" step="0.01" min="0" max="1">
                    </div>
                    <div class="form-group">
                        <label for="买回保障金比例">买回保障金比例</label>
                        <input type="number" id="买回保障金比例" name="买回保障金比例" value="{}" step="0.01" min="0" max="1">
                    </div>
                    
                    <button type="submit" class="btn">保存设置</button>
                </form>
            </div>
        """.format(
            self.策略.大象委托量阈值,
            self.策略.大象价差阈值,
            self.策略.大象确认次数,
            self.策略.价格偏移量,
            self.策略.卖出偏移量倍数,
            self.策略.买入偏移量倍数,
            self.策略.股票池比例,
            self.策略.买回保障金比例
        )
        
        return 内容
    
    def _日志页面(self) -> str:
        """生成日志页面内容"""
        内容 = """
            <div class="section">
                <h2>运行日志</h2>
                <table>
                    <tr>
                        <th>时间</th>
                        <th>消息</th>
                    </tr>
        """
        
        for 日志项 in reversed(self.日志):
            内容 += f"""
                <tr>
                    <td>{日志项["时间"]}</td>
                    <td>{日志项["消息"]}</td>
                </tr>
            """
        
        内容 += """
                </table>
            </div>
            
            <div class="refresh">
                <button class="btn" onclick="refreshPage()">刷新页面</button>
            </div>
        """
        
        return 内容
    
    # 命令处理函数
    def _开始策略(self, 参数: Dict) -> str:
        """开始策略命令处理"""
        if not self.策略:
            return "错误: 未连接策略实例"
        
        try:
            self.策略.start()
            self.记录日志("通过网页管理器启动策略")
            return "策略已启动"
        except Exception as e:
            错误信息 = f"启动策略错误: {e}"
            self.记录日志(错误信息)
            return 错误信息
    
    def _停止策略(self, 参数: Dict) -> str:
        """停止策略命令处理"""
        if not self.策略:
            return "错误: 未连接策略实例"
        
        try:
            self.策略.stop()
            self.记录日志("通过网页管理器停止策略")
            return "策略已停止"
        except Exception as e:
            错误信息 = f"停止策略错误: {e}"
            self.记录日志(错误信息)
            return 错误信息
    
    def _更新参数(self, 参数: Dict) -> str:
        """更新策略参数命令处理"""
        if not self.策略:
            return "错误: 未连接策略实例"
        
        try:
            # 参数字典中的值是列表，需要取第一个元素
            参数更新 = {}
            for 键, 值列表 in 参数.items():
                if 键 == "cmd":
                    continue
                
                值 = 值列表[0]
                
                # 尝试转换为合适的类型
                if "." in 值:
                    参数更新[键] = float(值)
                elif 值.isdigit():
                    参数更新[键] = int(值)
                else:
                    参数更新[键] = 值
            
            # 更新策略参数
            for 键, 值 in 参数更新.items():
                if hasattr(self.策略, 键):
                    setattr(self.策略, 键, 值)
                    self.记录日志(f"更新参数: {键} = {值}")
            
            # 如果策略正在运行，可能需要重新初始化某些组件
            if self.策略.trading:
                # 根据需要重新初始化组件
                pass
            
            return "参数已更新"
        except Exception as e:
            错误信息 = f"更新参数错误: {e}"
            self.记录日志(错误信息)
            return 错误信息 