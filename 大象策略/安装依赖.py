#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
大象策略依赖安装脚本
安装大象策略运行所需的所有依赖包
"""

import os
import sys
import subprocess

def 安装依赖(包名列表):
    """安装指定的依赖包"""
    print(f"开始安装依赖: {', '.join(包名列表)}")
    
    for 包名 in 包名列表:
        print(f"正在安装 {包名}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", 包名, "-U"])
            print(f"{包名} 安装成功！")
        except Exception as e:
            print(f"{包名} 安装失败: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("大象策略依赖安装程序")
    print("=" * 50)
    
    # 核心依赖
    核心依赖 = [
        "vnpy",
        "vnpy_ctastrategy",
        "vnpy_websocket"
    ]
    
    # Web界面依赖
    网页依赖 = [
        "flask",
        "flask_cors",
        "flask_socketio",
        "gevent",
        "gevent-websocket"
    ]
    
    # 数据处理依赖
    数据依赖 = [
        "numpy",
        "pandas",
        "matplotlib"
    ]
    
    print("安装核心依赖...")
    if 安装依赖(核心依赖):
        print("核心依赖安装完成！")
    else:
        print("核心依赖安装失败，请检查错误信息。")
        sys.exit(1)
    
    print("\n安装Web界面依赖...")
    if 安装依赖(网页依赖):
        print("Web界面依赖安装完成！")
    else:
        print("Web界面依赖安装失败，但不影响核心功能。")
    
    print("\n安装数据处理依赖...")
    if 安装依赖(数据依赖):
        print("数据处理依赖安装完成！")
    else:
        print("数据处理依赖安装失败，但不影响核心功能。")
    
    print("\n=" * 50)
    print("依赖安装完成！现在可以运行 启动.py 来启动策略。")
    print("=" * 50)
    
    input("按回车键退出...") 