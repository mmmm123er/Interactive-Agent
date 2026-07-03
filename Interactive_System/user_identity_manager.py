"""
用户身份管理模块
负责管理用户信息和行为偏好
"""

import os
import json
from datetime import datetime
from pathlib import Path


class UserIdentityManager:
    """
    用户身份管理器
    负责读取和更新用户信息文档
    """
    
    def __init__(self, data_dir="usr-identity-info"):
        """
        初始化用户身份管理器
        
        Args:
            data_dir (str): 用户数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
    def get_user_info(self, user_id):
        """
        获取用户信息
        
        Args:
            user_id (str): 用户ID
            
        Returns:
            dict: 用户信息字典，如果不存在则返回None
        """
        user_file = self.data_dir / f"{user_id}.md"
        
        if not user_file.exists():
            return None
            
        with open(user_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 解析用户信息
        return self._parse_user_info(content, user_id)
    
    def _parse_user_info(self, content, user_id):
        """
        解析用户信息文档内容
        
        Args:
            content (str): 文档内容
            user_id (str): 用户ID
            
        Returns:
            dict: 解析后的用户信息
        """
        lines = content.strip().split('\n')
        user_info = {
            'user_id': user_id,
            'name': '',
            'preferences': [],
            'behavior_patterns': [],
            'last_updated': ''
        }
        
        current_section = ''
        for line in lines:
            line = line.strip()
            if line.startswith('# 用户信息'):
                continue
            elif line.startswith('## 姓名'):
                current_section = 'name'
            elif line.startswith('## 偏好'):
                current_section = 'preferences'
            elif line.startswith('## 行为模式'):
                current_section = 'behavior_patterns'
            elif line.startswith('## 更新时间'):
                current_section = 'last_updated'
            else:
                if current_section == 'name' and line and not line.startswith('#'):
                    user_info['name'] = line
                elif current_section == 'preferences' and line and not line.startswith('#'):
                    user_info['preferences'].append(line)
                elif current_section == 'behavior_patterns' and line and not line.startswith('#'):
                    user_info['behavior_patterns'].append(line)
                elif current_section == 'last_updated' and line and not line.startswith('#'):
                    user_info['last_updated'] = line
                    
        return user_info
    
    def create_new_user(self, user_id):
        """
        创建新用户信息文档
        
        Args:
            user_id (str): 用户ID
        """
        user_file = self.data_dir / f"{user_id}.md"
        
        template = f"""# 用户信息
## 姓名

## 偏好

## 行为模式

## 更新时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(user_file, 'w', encoding='utf-8') as f:
            f.write(template)
    
    def update_user_info(self, user_id, name=None, preferences=None, behavior_patterns=None):
        """
        更新用户信息
        
        Args:
            user_id (str): 用户ID
            name (str): 用户姓名
            preferences (list): 用户偏好列表
            behavior_patterns (list): 用户行为模式列表
        """
        user_file = self.data_dir / f"{user_id}.md"
        
        if not user_file.exists():
            self.create_new_user(user_id)
            
        # 读取现有信息
        current_info = self.get_user_info(user_id)
        
        # 准备更新内容
        content_lines = [
            "# 用户信息",
            "## 姓名",
            name or current_info['name'] if current_info else "",
            "",
            "## 偏好"
        ]
        
        # 合并现有偏好和新偏好
        all_preferences = set(current_info['preferences'] if current_info else [])
        if preferences:
            for pref in preferences:
                all_preferences.add(pref)
        content_lines.extend(list(all_preferences))
        content_lines.append("")
        
        content_lines.extend([
            "## 行为模式"
        ])
        
        # 合并现有行为模式和新行为模式
        all_behaviors = set(current_info['behavior_patterns'] if current_info else [])
        if behavior_patterns:
            for behavior in behavior_patterns:
                all_behaviors.add(behavior)
        content_lines.extend(list(all_behaviors))
        content_lines.append("")
        
        content_lines.extend([
            "## 更新时间",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])
        
        # 写入更新后的内容
        with open(user_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))