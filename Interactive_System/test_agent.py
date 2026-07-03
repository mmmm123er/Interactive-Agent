"""
测试脚本
用于验证Agent系统的基本功能
"""

from main_agent import InteractiveAgent


def test_basic_functionality():
    """
    测试Agent的基本功能
    """
    print("=" * 50)
    print("开始测试交互式Agent系统")
    print("=" * 50)
    
    # 创建Agent实例
    agent = InteractiveAgent()
    print("✓ Agent初始化成功")
    
    # 模拟用户交互
    print("\n模拟用户交互...")
    
    # 模拟音频和图像输入
    audio_input = "sample_audio_for_user_12345"
    image_data = "sample_image_data"
    
    # 处理交互
    response = agent.process_interaction(audio_input, image_data)
    print(f"✓ Agent响应: {response}")
    
    # 验证用户信息是否被正确创建或更新
    user_info = agent.user_manager.get_user_info("user_12345")
    if user_info:
        print(f"✓ 用户信息已创建/更新: {user_info['user_id']}")
    else:
        print("✗ 用户信息未找到")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


def test_modules_individually():
    """
    单独测试各个模块
    """
    print("\n" + "-" * 30)
    print("测试各个模块")
    print("-" * 30)
    
    # 测试用户身份管理
    from user_identity_manager import UserIdentityManager
    user_mgr = UserIdentityManager()
    print("✓ 用户身份管理模块正常")
    
    # 测试声纹识别接口
    from voice_recognition_interface import VoiceRecognitionInterface
    voice_iface = VoiceRecognitionInterface()
    user_id = voice_iface.recognize_user("test_audio")
    print(f"✓ 声纹识别接口正常，返回用户ID: {user_id}")
    
    # 测试多模态分析
    from multimodal_analyzer import MultimodalAnalyzer
    mm_analyzer = MultimodalAnalyzer()
    greeting = mm_analyzer.analyze_user_and_greet("test_image", {"name": "张三"})
    print(f"✓ 多模态分析模块正常，返回问候: {greeting}")
    
    # 测试意图分类
    from intent_classifier import IntentClassifier
    intent_clf = IntentClassifier()
    intent, conf = intent_clf.classify_intent("请帮我播放音乐")
    print(f"✓ 意图分类模块正常，意图: {intent}, 置信度: {conf}")
    
    # 测试RAG工具检索
    from rag_tool_retriever import RagToolRetriever
    rag_retriever = RagToolRetriever()
    tools = rag_retriever.retrieve_tools_by_intent("播放音乐")
    print(f"✓ RAG工具检索模块正常，找到 {len(tools)} 个相关工具")


if __name__ == "__main__":
    test_modules_individually()
    test_basic_functionality()