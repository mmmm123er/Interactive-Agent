"""
AI模型接口模块
提供与大模型交互的接口
可用于意图识别等任务
"""


def mock_ai_intent_classification(text):
    """
    模拟AI模型的意图分类功能
    在实际应用中，这将被替换为真实的大模型调用
    
    Args:
        text (str): 输入文本
        
    Returns:
        dict: 包含意图类型和置信度的结果
    """
    # 这里模拟大模型的响应
    # 在实际实现中，这里会调用真实的大模型API
    
    # 简单规则模拟大模型的判断
    text_lower = text.lower()
    
    # 包含任务关键词的可能性较高
    task_indicators = ['帮我', '请帮我', '执行', '打开', '关闭', '播放', '设置', '查找', '搜索']
    chat_indicators = ['你好', '您好', '怎么样', '好吗', '聊聊', '聊天', '谢谢', '感谢']
    
    task_count = sum(1 for indicator in task_indicators if indicator in text_lower)
    chat_count = sum(1 for indicator in chat_indicators if indicator in text_lower)
    
    if task_count > chat_count:
        return {
            'intent': 'task',
            'confidence': min(0.5 + task_count * 0.2, 1.0),
            'explanation': '检测到任务请求关键词'
        }
    elif chat_count > 0:
        return {
            'intent': 'chat',
            'confidence': min(0.5 + chat_count * 0.15, 1.0),
            'explanation': '检测到社交或问候语'
        }
    else:
        # 默认情况，根据句子长度和结构判断
        words = text.split()
        if len(words) <= 3:
            return {
                'intent': 'chat',
                'confidence': 0.6,
                'explanation': '短句，倾向社交语句'
            }
        else:
            return {
                'intent': 'chat',
                'confidence': 0.5,
                'explanation': '无明显指示，保持默认'
            }


class AIModelInterface:
    """
    AI模型接口类
    封装与大模型的交互
    """
    
    def __init__(self):
        """
        初始化AI模型接口
        """
        # 如果需要初始化模型连接，在这里进行
        pass
    
    def classify_intent_with_ai(self, text):
        """
        使用AI模型分类用户意图
        
        Args:
            text (str): 用户输入文本
            
        Returns:
            tuple: (intent_type, confidence_score)
                   intent_type: 'chat' 或 'task'
                   confidence_score: 置信度分数 (0-1)
        """
        result = mock_ai_intent_classification(text)
        return result['intent'], result['confidence']
    
    def analyze_conversation_context(self, conversation_history):
        """
        分析对话上下文
        
        Args:
            conversation_history (list): 对话历史列表
            
        Returns:
            dict: 上下文分析结果
        """
        # 模拟分析对话上下文
        if not conversation_history:
            return {'current_topic': 'greeting', 'topic_confidence': 1.0}
        
        # 简单分析最近几次对话的主题
        recent_texts = conversation_history[-3:]  # 考虑最近3次对话
        task_related = sum(1 for text in recent_texts if any(kw in text.lower() 
                     for kw in ['帮我', '执行', '播放', '设置', '查找']))
        
        if task_related >= 2:
            return {'current_topic': 'task_execution', 'topic_confidence': 0.8}
        else:
            return {'current_topic': 'social_chat', 'topic_confidence': 0.7}