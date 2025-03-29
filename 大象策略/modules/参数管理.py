#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
参数管理模块 - 支持每个品种单独设置参数
"""
from typing import Dict, List, Any, Optional
import os
import json
from datetime import datetime
import copy


class 参数管理器:
    """参数管理器类，支持全局参数和品种特定参数"""
    
    def __init__(self, 配置目录: str = "config"):
        """
        初始化参数管理器
        
        参数:
            配置目录: 配置文件目录
        """
        # 获取当前文件所在目录
        当前目录 = os.path.dirname(os.path.abspath(__file__))
        
        # 配置目录可能是相对路径或绝对路径
        if os.path.isabs(配置目录):
            self.配置目录 = 配置目录
        else:
            # 如果是相对路径，则相对于当前文件所在目录
            self.配置目录 = os.path.join(当前目录, 配置目录)
        
        print(f"参数管理器初始化，配置目录: {self.配置目录}")
        
        self.全局参数 = {}
        self.品种参数 = {}
        
        # 确保配置目录存在
        os.makedirs(self.配置目录, exist_ok=True)
        
        # 配置文件路径
        self.全局参数文件 = os.path.join(self.配置目录, "global_params.json")
        self.品种参数文件 = os.path.join(self.配置目录, "symbol_params.json")
        self.股票列表文件 = os.path.join(self.配置目录, "stocks.json")
        
        print(f"配置文件路径:")
        print(f" - 全局参数文件: {self.全局参数文件}")
        print(f" - 品种参数文件: {self.品种参数文件}")
        print(f" - 股票列表文件: {self.股票列表文件}")
        
        # 加载配置
        self._加载配置()
    
    def _加载配置(self):
        """加载全局和品种特定配置"""
        # 加载全局参数
        if os.path.exists(self.全局参数文件):
            try:
                with open(self.全局参数文件, "r", encoding="utf-8") as f:
                    self.全局参数 = json.load(f)
                print(f"成功加载全局参数: {self.全局参数}")
            except Exception as e:
                print(f"加载全局参数出错: {e}")
                # 如果加载失败，使用空字典
                self.全局参数 = {}
        else:
            # 文件不存在，初始化为空字典
            self.全局参数 = {}
            print(f"全局参数文件不存在，初始化为空")
            # 创建配置文件
            try:
                with open(self.全局参数文件, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=4, ensure_ascii=False)
                print(f"已创建空的全局参数文件")
            except Exception as e:
                print(f"创建全局参数文件失败: {e}")
        
        # 加载品种特定参数
        if os.path.exists(self.品种参数文件):
            try:
                with open(self.品种参数文件, "r", encoding="utf-8") as f:
                    self.品种参数 = json.load(f)
                print(f"成功加载品种参数: {self.品种参数}")
            except Exception as e:
                print(f"加载品种参数出错: {e}")
                # 如果加载失败，使用空字典
                self.品种参数 = {}
        else:
            # 文件不存在，初始化为空字典
            self.品种参数 = {}
            print(f"品种参数文件不存在，初始化为空")
            # 创建配置文件
            try:
                with open(self.品种参数文件, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=4, ensure_ascii=False)
                print(f"已创建空的品种参数文件")
            except Exception as e:
                print(f"创建品种参数文件失败: {e}")
    
    def _保存配置(self):
        """保存参数配置到文件"""
        # 保存全局参数
        try:
            with open(self.全局参数文件, "w", encoding="utf-8") as f:
                json.dump(self.全局参数, f, indent=4, ensure_ascii=False)
            print(f"已保存全局参数到 {self.全局参数文件}")
        except Exception as e:
            print(f"保存全局参数出错: {e}")
        
        # 保存品种特定参数
        try:
            with open(self.品种参数文件, "w", encoding="utf-8") as f:
                json.dump(self.品种参数, f, indent=4, ensure_ascii=False)
            print(f"已保存品种参数到 {self.品种参数文件}")
        except Exception as e:
            print(f"保存品种参数出错: {e}")
    
    def 设置全局参数(self, 模块: str, 参数名: str, 参数值: Any):
        """
        设置全局参数
        
        参数:
            模块: 参数所属模块，如'大象识别'、'交易执行'等
            参数名: 参数名称
            参数值: 参数值
        """
        if 模块 not in self.全局参数:
            self.全局参数[模块] = {}
        
        self.全局参数[模块][参数名] = 参数值
        self._保存配置()
    
    def 设置品种参数(self, 品种代码: str, 模块: str, 参数名: str, 参数值: Any):
        """
        设置品种特定参数
        
        参数:
            品种代码: 股票代码
            模块: 参数所属模块
            参数名: 参数名称
            参数值: 参数值
        """
        print(f"设置品种参数: {品种代码}, 模块: {模块}, 参数名: {参数名}, 参数值: {参数值}")
        
        if 品种代码 not in self.品种参数:
            print(f"品种代码 {品种代码} 不存在于品种参数中，创建新条目")
            self.品种参数[品种代码] = {}
        
        if 模块 not in self.品种参数[品种代码]:
            print(f"模块 {模块} 不存在于品种 {品种代码} 参数中，创建新条目")
            self.品种参数[品种代码][模块] = {}
        
        self.品种参数[品种代码][模块][参数名] = 参数值
        print(f"更新后的品种参数: {self.品种参数}")
        self._保存配置()
        print("配置已保存")
    
    def 获取参数(self, 品种代码: str, 模块: str, 参数名: str, 默认值: Any = None) -> Any:
        """
        获取参数，优先使用品种特定参数，如果不存在则使用全局参数
        
        参数:
            品种代码: 股票代码
            模块: 参数所属模块
            参数名: 参数名称
            默认值: 如果参数不存在则返回默认值
            
        返回:
            参数值
        """
        # 检查是否有品种特定参数
        if (品种代码 in self.品种参数 and
            模块 in self.品种参数[品种代码] and
            参数名 in self.品种参数[品种代码][模块]):
            return self.品种参数[品种代码][模块][参数名]
        
        # 检查是否有全局参数
        if 模块 in self.全局参数 and 参数名 in self.全局参数[模块]:
            return self.全局参数[模块][参数名]
        
        # 返回默认值
        return 默认值
    
    def 获取品种所有参数(self, 品种代码: str) -> Dict:
        """
        获取品种的所有参数（合并全局参数和品种特定参数）
        
        参数:
            品种代码: 股票代码
            
        返回:
            参数字典，包含一个特殊的_品种特定参数标记字段，指示哪些品种有特定参数
        """
        print(f"调用获取品种所有参数: {品种代码}")
        print(f"全局参数: {self.全局参数}")
        print(f"品种参数: {self.品种参数}")
        
        # 深拷贝全局参数作为基础
        结果 = copy.deepcopy(self.全局参数)
        
        # 确保结果中至少包含基本模块结构
        if "大象识别" not in 结果:
            结果["大象识别"] = {}
        if "交易执行" not in 结果:
            结果["交易执行"] = {}
        if "风险控制" not in 结果:
            结果["风险控制"] = {}
        if "资金管理" not in 结果:
            结果["资金管理"] = {}
        
        # 添加一个特殊字段，标记哪些品种有特定参数
        结果["_品种特定参数标记"] = {}
        for 代码 in self.品种参数.keys():
            结果["_品种特定参数标记"][代码] = True
        
        # 如果有品种特定参数，合并到结果中
        if 品种代码 in self.品种参数:
            print(f"存在品种特定参数: {self.品种参数[品种代码]}")
            for 模块, 模块参数 in self.品种参数[品种代码].items():
                if 模块 not in 结果:
                    结果[模块] = {}
                结果[模块].update(模块参数)
        
        print(f"返回参数: {结果}")
        return 结果
    
    def 删除品种参数(self, 品种代码: str, 模块: str = None, 参数名: str = None):
        """
        删除品种特定参数
        
        参数:
            品种代码: 股票代码
            模块: 参数所属模块，如果为None则删除该品种所有参数
            参数名: 参数名称，如果为None则删除该模块所有参数
        """
        if 品种代码 not in self.品种参数:
            return
        
        if 模块 is None:
            # 删除该品种所有参数
            del self.品种参数[品种代码]
        elif 模块 in self.品种参数[品种代码]:
            if 参数名 is None:
                # 删除该模块所有参数
                del self.品种参数[品种代码][模块]
            elif 参数名 in self.品种参数[品种代码][模块]:
                # 删除特定参数
                del self.品种参数[品种代码][模块][参数名]
        
        self._保存配置()
    
    def 导入参数(self, 参数数据: Dict):
        """
        从字典导入参数
        
        参数:
            参数数据: 包含全局参数和品种参数的字典
        """
        if "全局参数" in 参数数据:
            self.全局参数 = 参数数据["全局参数"]
        
        if "品种参数" in 参数数据:
            self.品种参数 = 参数数据["品种参数"]
        
        self._保存配置()
    
    def 导出参数(self) -> Dict:
        """
        导出所有参数
        
        返回:
            包含全局参数和品种参数的字典
        """
        return {
            "全局参数": self.全局参数,
            "品种参数": self.品种参数
        }
    
    def 初始化默认参数(self, 默认参数: Dict):
        """
        初始化默认参数，如果参数文件不存在则创建
        
        参数:
            默认参数: 默认参数字典
        """
        # 如果全局参数为空，设置默认值
        if not self.全局参数 and "全局参数" in 默认参数:
            self.全局参数 = 默认参数["全局参数"]
            self._保存配置()
    
    def 获取股票列表(self) -> List[str]:
        """
        获取交易股票列表
        
        返回:
            股票代码列表
        """
        if os.path.exists(self.股票列表文件):
            try:
                with open(self.股票列表文件, "r", encoding="utf-8") as f:
                    数据 = json.load(f)
                    股票列表 = 数据.get("stocks", [])
                    print(f"成功加载股票列表: {股票列表}")
                    return 股票列表
            except Exception as e:
                print(f"加载股票列表出错: {e}")
                return []
        else:
            # 文件不存在，创建空文件
            try:
                with open(self.股票列表文件, "w", encoding="utf-8") as f:
                    json.dump({"stocks": []}, f, indent=4, ensure_ascii=False)
                print(f"已创建空的股票列表文件")
            except Exception as e:
                print(f"创建股票列表文件失败: {e}")
        return []
    
    def 设置股票列表(self, 股票列表: List[str]):
        """
        设置交易股票列表
        
        参数:
            股票列表: 股票代码列表
        """
        print(f"设置股票列表: {股票列表}")
        try:
            with open(self.股票列表文件, "w", encoding="utf-8") as f:
                json.dump({"stocks": 股票列表}, f, indent=4, ensure_ascii=False)
            print(f"已保存股票列表到 {self.股票列表文件}")
        except Exception as e:
            print(f"保存股票列表出错: {e}")