"""
意图分类模块
用于识别用户意图（闲聊或任务执行）
使用AI模型或文本分类器
"""

from ai_model_interface import AIModelInterface


class IntentClassifier:
    """
    意图分类器
    采用状态机方式管理意图状态，使用AI模型进行意图识别
    """
    
    def __init__(self):
        """
        初始化意图分类器
        默认状态为闲聊
        """
        self.ai_model = AIModelInterface()
        
        # 初始状态为闲聊
        self.current_state = 'chat'  # 'chat' 或 'task'
    
    def set_state(self, state):
        """
        设置当前意图状态
        
        Args:
            state (str): 'chat' 或 'task'
        """
        if state in ['chat', 'task']:
            self.current_state = state
    
    def classify_intent(self, user_input, user_context=None):
        """
        分类用户意图，基于状态机和AI模型
        
        Args:
            user_input (str): 用户输入文本
            user_context (dict): 用户上下文信息（可选）
            
        Returns:
            tuple: (intent_type, confidence_score)
                   intent_type: 'chat' 或 'task'
                   confidence_score: 置信度分数 (0-1)
        """
        # 如果当前状态已经是任务状态，保持任务状态
        if self.current_state == 'task':
            return 'task', 1.0
        
        # 如果当前是闲聊状态，使用AI模型判断是否需要切换到任务状态
        intent_type, confidence = self.ai_model.classify_intent_with_ai(user_input)
        
        if intent_type == 'task':
            # 检测到任务意图，切换到任务状态
            self.current_state = 'task'
            return 'task', confidence
        else:
            # 保持闲聊状态
            return 'chat', confidence
    
    def extract_task_details(self, user_input):
        """
        从用户输入中提取任务详情
        
        Args:
            user_input (str): 用户输入文本
            
        Returns:
            dict: 包含任务相关信息的字典
        """
        # 定义任务相关的关键词
        task_keywords = [
            '做', '执行', '运行', '启动', '打开', '关闭', '停止', '开始',
            '完成', '结束', '处理', '解决', '帮助', '帮我', '请帮我',
            '可以帮我', '想要', '需要', '给我', '设置', '配置', '调整',
            '查找', '搜索', '找到', '获取', '下载', '上传', '发送',
            '删除', '新建', '创建', '修改', '编辑', '更新', '同步',
            '播放', '暂停', '继续', '跳过', '重播', '下一首', '上一首',
            '打电话', '发短信', '发邮件', '写', '记', '提醒', '通知',
            '翻译', '计算', '统计', '分析', '整理', '排序', '过滤',
            '连接', '断开', '切换', '转换', '格式化', '备份', '恢复',
            '安装', '卸载', '升级', '降级', '重启', '关机', '休眠',
            '拍照', '录像', '截图', '录屏', '扫描', '识别', '检测'
        ]
        
        # 使用正则表达式提取任务关键词和目标
        task_info = {
            'action': None,
            'target': None,
            'details': []
        }
        
        # 查找动词（动作）
        for keyword in task_keywords:
            if keyword in user_input:
                task_info['action'] = keyword
                break
        
        # 提取可能的目标对象
        # 移除动作关键词，剩下的可能是目标
        remaining_text = user_input
        if task_info['action']:
            remaining_text = remaining_text.replace(task_info['action'], '', 1)
        
        # 提取剩余文本中的关键名词作为目标
        # 简单的提取方式，实际实现中可能需要更复杂的NLP技术
        target_words = [word.strip() for word in remaining_text.split() if len(word.strip()) > 1]
        if target_words:
            task_info['target'] = ' '.join(target_words[:3])  # 取前三个词作为目标
        
        return task_info
    
    def reset_to_chat_state(self):
        """
        重置状态为闲聊模式
        """
        self.current_state = 'chat'