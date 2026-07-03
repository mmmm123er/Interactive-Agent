"""
状态机测试脚本
测试意图分类器的状态切换功能
"""

from main_agent import InteractiveAgent
from intent_classifier import IntentClassifier


def test_state_machine():
    """
    测试意图分类器的状态切换机制
    """
    print("=" * 50)
    print("测试意图分类器状态机功能")
    print("=" * 50)
    
    # 创建意图分类器实例
    intent_clf = IntentClassifier()
    
    print(f"初始状态: {intent_clf.current_state}")
    
    # 测试1: 闲聊输入，状态应保持为chat
    response1 = intent_clf.classify_intent("你好，今天天气怎么样？")
    print(f"输入: '你好，今天天气怎么样？' -> 意图: {response1[0]}, 状态: {intent_clf.current_state}")
    
    # 测试2: 另一个闲聊输入，状态仍应为chat
    response2 = intent_clf.classify_intent("你最近好吗？")
    print(f"输入: '你最近好吗？' -> 意图: {response2[0]}, 状态: {intent_clf.current_state}")
    
    # 测试3: 任务输入，状态应切换为task
    response3 = intent_clf.classify_intent("请帮我播放音乐")
    print(f"输入: '请帮我播放音乐' -> 意图: {response3[0]}, 状态: {intent_clf.current_state}")
    
    # 测试4: 之后即使输入闲聊内容，状态也应保持为task
    response4 = intent_clf.classify_intent("你好吗？")
    print(f"输入: '你好吗？' -> 意图: {response4[0]}, 状态: {intent_clf.current_state}")
    
    # 测试5: 再次输入任务，状态继续为task
    response5 = intent_clf.classify_intent("现在请帮我关闭音乐")
    print(f"输入: '现在请帮我关闭音乐' -> 意图: {response5[0]}, 状态: {intent_clf.current_state}")
    
    print("\n" + "=" * 50)
    print("状态切换测试完成")
    print("=" * 50)


def simulate_conversation():
    """
    模拟连续对话场景
    """
    print("\n" + "=" * 50)
    print("模拟连续对话场景")
    print("=" * 50)
    
    # 创建Agent实例
    agent = InteractiveAgent()
    
    # 模拟连续的交互过程
    interactions = [
        ("你好，今天天气怎么样？", "sample_audio_1", "sample_image_1"),
        ("请帮我播放音乐", "sample_audio_2", "sample_image_2"),
        ("你好吗？", "sample_audio_3", "sample_image_3"),
        ("音量调大一点", "sample_audio_4", "sample_image_4")
    ]
    
    for i, (text, audio, image) in enumerate(interactions, 1):
        print(f"\n第{i}次交互 - 输入: '{text}'")
        
        # 临时修改语音转文字方法以返回当前交互的文本
        agent._convert_audio_to_text = lambda x, current_text=text: current_text
        
        # 修复lambda函数以捕获当前的text值
        agent._convert_audio_to_text = lambda x, ct=text: ct
        
        response = agent.process_interaction(audio, image)
        print(f"响应: {response}")
        print(f"当前意图状态: {agent.intent_classifier.current_state}")
        
        # 恢复原始方法（虽然在这里不需要，但为了清晰起见）
        original_method = getattr(agent, '_original_convert', agent._convert_audio_to_text)
    
    print("\n" + "=" * 50)
    print("连续对话模拟完成")
    print("=" * 50)


def test_full_agent_with_states():
    """
    测试完整Agent的状态管理
    """
    # 由于Python闭包的特殊性，我们需要重新定义此函数
    print("\n" + "=" * 50)
    print("测试完整Agent状态管理")
    print("=" * 50)
    
    # 创建Agent实例
    agent = InteractiveAgent()
    
    # 为agent添加一个辅助方法来设置语音转文字返回值
    def set_next_response(text):
        agent._convert_audio_to_text = lambda x, current_text=text: current_text
    
    print("第一次交互 - 闲聊输入:")
    set_next_response("你好，今天天气怎么样？")
    response1 = agent.process_interaction("sample_audio_1", "sample_image_1")
    print(f"响应: {response1}")
    print(f"当前意图状态: {agent.intent_classifier.current_state}")
    
    print("\n第二次交互 - 任务输入:")
    set_next_response("请帮我播放音乐")
    response2 = agent.process_interaction("sample_audio_2", "sample_image_2")
    print(f"响应: {response2}")
    print(f"当前意图状态: {agent.intent_classifier.current_state}")
    
    print("\n第三次交互 - 闲聊输入，但应仍为任务状态:")
    set_next_response("你好吗？")
    response3 = agent.process_interaction("sample_audio_3", "sample_image_3")
    print(f"响应: {response3}")
    print(f"当前意图状态: {agent.intent_classifier.current_state}")
    
    print("\n第四次交互 - 任务输入，继续保持任务状态:")
    set_next_response("音量调大一点")
    response4 = agent.process_interaction("sample_audio_4", "sample_image_4")
    print(f"响应: {response4}")
    print(f"当前意图状态: {agent.intent_classifier.current_state}")
    
    print("\n" + "=" * 50)
    print("完整Agent状态管理测试完成")
    print("=" * 50)


if __name__ == "__main__":
    test_state_machine()
    test_full_agent_with_states()