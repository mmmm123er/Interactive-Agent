"""
RAG工具检索模块
根据用户意图检索相关的MCP工具
"""

import os
from pathlib import Path
import json


class RagToolRetriever:
    """
    RAG工具检索器
    根据用户意图检索最相关的工具
    """
    
    def __init__(self, tools_dir="mcp_tools", top_k=5):
        """
        初始化RAG工具检索器
        
        Args:
            tools_dir (str): 工具描述文件存储目录
            top_k (int): 返回最相关的工具数量
        """
        self.tools_dir = Path(tools_dir)
        self.top_k = top_k
        self.tools_index = {}
        self._load_tools()
    
    def _load_tools(self):
        """
        加载所有可用的工具描述
        """
        if not self.tools_dir.exists():
            print(f"[警告] 工具目录 {self.tools_dir} 不存在")
            return
        
        # 从目录中加载所有工具描述文件
        for tool_file in self.tools_dir.glob("*.json"):
            try:
                with open(tool_file, 'r', encoding='utf-8') as f:
                    tool_desc = json.load(f)
                    tool_name = tool_file.stem
                    self.tools_index[tool_name] = tool_desc
            except Exception as e:
                print(f"[错误] 加载工具文件 {tool_file} 时出错: {e}")
    
    def retrieve_tools_by_intent(self, user_intent, task_details=None):
        """
        根据用户意图检索相关工具
        
        Args:
            user_intent (str): 用户意图描述
            task_details (dict): 任务详细信息（可选）
            
        Returns:
            list: 相关工具列表，按相关性排序
        """
        # 计算用户意图与各工具的相关性
        intent_lower = user_intent.lower()
        scored_tools = []
        
        for tool_name, tool_desc in self.tools_index.items():
            score = self._calculate_relevance_score(intent_lower, tool_desc, task_details)
            scored_tools.append((tool_name, tool_desc, score))
        
        # 按相关性分数排序并返回top_k个工具
        scored_tools.sort(key=lambda x: x[2], reverse=True)
        return scored_tools[:self.top_k]
    
    def _calculate_relevance_score(self, user_intent, tool_desc, task_details=None):
        """
        计算用户意图与工具的相关性分数
        
        Args:
            user_intent (str): 用户意图
            tool_desc (dict): 工具描述
            task_details (dict): 任务详细信息
            
        Returns:
            float: 相关性分数 (0-1)
        """
        score = 0.0
        
        # 检查工具描述中的关键词匹配
        desc_text = f"{tool_desc.get('name', '')} {tool_desc.get('description', '')} {' '.join(tool_desc.get('keywords', []))}".lower()
        
        # 计算关键词匹配数量
        intent_words = user_intent.split()
        matched_keywords = [word for word in intent_words if word in desc_text]
        
        if len(intent_words) > 0:
            score += len(matched_keywords) / len(intent_words) * 0.7  # 关键词匹配占比
        
        # 如果提供了任务细节，也考虑任务细节的匹配
        if task_details and 'target' in task_details and task_details['target']:
            target = task_details['target'].lower()
            if target in desc_text:
                score += 0.3  # 目标匹配奖励
        
        return min(score, 1.0)  # 确保分数不超过1
    
    def get_tool_names(self):
        """
        获取所有可用工具的名称
        
        Returns:
            list: 工具名称列表
        """
        return list(self.tools_index.keys())
    
    def get_tool_description(self, tool_name):
        """
        获取指定工具的描述
        
        Args:
            tool_name (str): 工具名称
            
        Returns:
            dict: 工具描述，如果不存在则返回None
        """
        return self.tools_index.get(tool_name)