#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志模块 - 提供日志记录功能
"""
import logging
import os
import sys
from datetime import datetime

# 日志格式
日志格式 = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
日期格式 = "%Y-%m-%d %H:%M:%S"

# 日志级别映射
日志级别 = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# 日志输出目录
日志目录 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(日志目录):
    os.makedirs(日志目录)

# 全局日志配置设置标志
已配置 = False

def 配置日志(级别="info", 控制台输出=True, 文件输出=True):
    """
    配置日志系统
    
    参数:
        级别: 日志级别，可选值为debug, info, warning, error, critical
        控制台输出: 是否输出到控制台
        文件输出: 是否输出到文件
    """
    global 已配置
    if 已配置:
        return
    
    # 获取根日志记录器
    根日志 = logging.getLogger()
    根日志.setLevel(日志级别.get(级别.lower(), logging.INFO))
    
    # 清除现有处理器
    for hdlr in 根日志.handlers[:]:
        根日志.removeHandler(hdlr)
    
    # 设置控制台输出
    if 控制台输出:
        控制台处理器 = logging.StreamHandler(sys.stdout)
        控制台处理器.setFormatter(logging.Formatter(日志格式, 日期格式))
        根日志.addHandler(控制台处理器)
    
    # 设置文件输出
    if 文件输出:
        日期字符串 = datetime.now().strftime("%Y%m%d")
        日志文件 = os.path.join(日志目录, f"大象策略_{日期字符串}.log")
        文件处理器 = logging.FileHandler(日志文件, encoding='utf-8')
        文件处理器.setFormatter(logging.Formatter(日志格式, 日期格式))
        根日志.addHandler(文件处理器)
    
    已配置 = True
    根日志.info("日志系统已配置完成")

def get_logger(名称, 级别=None, 控制台输出=True, 文件输出=True, 文件名=None):
    """
    获取指定名称的日志记录器
    
    参数:
        名称: 日志记录器名称
        级别: 日志级别，可以是logging模块的级别常量或字符串
        控制台输出: 是否输出到控制台
        文件输出: 是否输出到文件
        文件名: 日志文件名，如果为None则使用默认格式
        
    返回:
        日志记录器对象
    """
    # 确保日志系统已配置
    if not 已配置:
        配置日志()
    
    # 获取指定名称的日志记录器
    日志记录器 = logging.getLogger(名称)
    
    # 如果指定了级别，则设置
    if 级别 is not None:
        # 如果级别是字符串，转换为对应的常量
        if isinstance(级别, str):
            级别 = 日志级别.get(级别.lower(), logging.INFO)
        日志记录器.setLevel(级别)
    
    # 如果需要特定的文件处理器，添加它
    if 文件输出 and 文件名:
        # 检查是否已经有同名文件处理器
        有文件处理器 = False
        for handler in 日志记录器.handlers:
            if isinstance(handler, logging.FileHandler) and handler.baseFilename.endswith(文件名):
                有文件处理器 = True
                break
                
        if not 有文件处理器:
            日志文件 = os.path.join(日志目录, 文件名)
            文件处理器 = logging.FileHandler(日志文件, encoding='utf-8')
            文件处理器.setFormatter(logging.Formatter(日志格式, 日期格式))
            日志记录器.addHandler(文件处理器)
    
    return 日志记录器 