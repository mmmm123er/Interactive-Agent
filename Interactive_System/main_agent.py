"""
主Agent控制器
整合各个模块，实现完整的交互流程
"""

from user_identity_manager import UserIdentityManager
from voice_recognition_interface import VoiceRecognitionInterface
from multimodal_analyzer import MultimodalAnalyzer
from intent_classifier import IntentClassifier
from rag_tool_retriever import RagToolRetriever


class InteractiveAgent:
    """
    交互式Agent主控制器
    整合所有模块实现完整的对话和任务执行功能
    """
    
    def __init__(self):
        """
        初始化主Agent
        """
        self.user_manager = UserIdentityManager()
        self.voice_recognizer = VoiceRecognitionInterface()
        self.multimodal_analyzer = MultimodalAnalyzer()
        self.intent_classifier = IntentClassifier()
        self.rag_retriever = RagToolRetriever()
        
        # 保存当前会话的用户信息
        self.current_user_id = None
        self.current_user_context = None
        
        # 添加状态管理标志
        self.session_started = False  # 标记会话是否已开始
    
    def process_interaction(self, audio_input, image_data):
        """
        处理一次完整的交互流程
        
        Args:
            audio_input: 音频输入数据
            image_data: 图像输入数据
            
        Returns:
            str: Agent的响应
        """
        # 步骤1: 使用声纹识别获取用户ID
        user_id = self.voice_recognizer.recognize_user(audio_input)
        self.current_user_id = user_id
        
        if not user_id:
            return "抱歉，我没有听清楚，请再说一遍。"
        
        # 步骤2: 检查用户信息是否存在
        user_info = self.user_manager.get_user_info(user_id)
        
        # 如果用户信息不存在，创建新的用户档案
        if not user_info:
            self.user_manager.create_new_user(user_id)
            user_info = self.user_manager.get_user_info(user_id)
            # 这里应该询问用户姓名，但为了简化，暂时跳过
            greeting_base = "您好！我是您的智能助手，很高兴认识您！请问您怎么称呼？"
        else:
            # 如果用户信息存在，构建个性化问候
            self.current_user_context = user_info
            greeting_base = self.multimodal_analyzer.analyze_user_and_greet(
                image_data, user_context=user_info
            )
        
        # 步骤3: 处理用户语音输入
        # 这里假设audio_input已经被转录为文本
        # 在实际实现中，你需要添加语音转文字的功能
        user_text = self._convert_audio_to_text(audio_input)
        
        # 步骤4: 分类用户意图
        # 如果这是会话的开始（首次交互），默认为闲聊模式
        if not self.session_started:
            # 初始化为闲聊状态
            self.intent_classifier.set_state('chat')
            self.session_started = True
        
        intent_type, confidence = self.intent_classifier.classify_intent(
            user_text, user_context=user_info
        )
        
        # 记录用户行为模式
        self._record_user_behavior(user_id, user_text, intent_type)
        
        # 步骤5: 根据意图类型生成响应
        if intent_type == 'chat':
            # 闲聊模式
            response = self._handle_chat_mode(greeting_base, user_text, user_info)
        else:
            # 任务模式
            response = self._handle_task_mode(user_text)
        
        return response
    
    def _convert_audio_to_text(self, audio_input):
        """
        将音频输入转换为文本
        这里只是一个模拟实现，实际应用中需要集成语音转文字服务
        
        Args:
            audio_input: 音频输入数据
            
        Returns:
            str: 转换后的文本
        """
        # 模拟语音转文字
        print(f"[语音转文字] 正在转换音频输入...")
        # 在实际应用中，这里应该调用ASR服务
        return "你好，请帮我播放音乐"  # 示例文本
    
    def _record_user_behavior(self, user_id, user_input, intent_type):
        """
        记录用户行为模式和偏好
        
        Args:
            user_id (str): 用户ID
            user_input (str): 用户输入
            intent_type (str): 意图类型
        """
        # 提取用户偏好和行为模式的关键信息
        preferences = []
        behavior_patterns = [f"通常在交互中表达: {user_input[:50]}..."]
        
        if intent_type == 'task':
            behavior_patterns.append("倾向于请求执行具体任务")
        else:
            behavior_patterns.append("倾向于进行社交闲聊")
        
        # 更新用户信息
        self.user_manager.update_user_info(
            user_id,
            preferences=preferences,
            behavior_patterns=behavior_patterns
        )
    
    def _handle_chat_mode(self, greeting, user_text, user_info):
        """
        处理闲聊模式
        
        Args:
            greeting (str): 问候语
            user_text (str): 用户输入文本
            user_info (dict): 用户信息
            
        Returns:
            str: 闲聊响应
        """
        # 构建个性化响应
        if user_info and user_info.get('name'):
            response = f"{greeting} 我们来聊聊天吧！您说：{user_text}"
        else:
            response = f"{greeting} 很高兴和您聊天！您说：{user_text}"
        
        return response
    
    def _handle_task_mode(self, user_text):
        """
        处理任务模式
        
        Args:
            user_text (str): 用户输入文本
            
        Returns:
            str: 任务执行响应
        """
        # 提取任务详情
        task_details = self.intent_classifier.extract_task_details(user_text)
        
        # 使用RAG检索相关工具
        relevant_tools = self.rag_retriever.retrieve_tools_by_intent(
            user_text, task_details
        )
        
        if relevant_tools:
            # 选择第一个最相关的工具
            selected_tool = relevant_tools[0]
            task_name = selected_tool[1].get('name', '未命名任务')
            response = f"好的，下面我将执行：{task_name}"
        else:
            # 如果没有找到合适的工具，返回通用响应
            response = "好的，我理解您需要我执行一些任务，但目前没有找到合适的工具来完成这个任务。"
        
        return response


def main():
    """
    主函数，用于测试Agent功能
    """
    print("初始化交互式Agent...")
    agent = InteractiveAgent()
    
    # 模拟输入数据
    audio_input = "sample_audio_data"  # 实际应用中这将是音频数据
    image_data = "sample_image_data"   # 实际应用中这将是图像数据
    
    # 处理交互
    response = agent.process_interaction(audio_input, image_data)
    print(f"Agent响应: {response}")


if __name__ == "__main__":
    main()