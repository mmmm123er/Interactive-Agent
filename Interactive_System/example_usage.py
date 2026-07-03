"""
使用示例
展示如何使用交互式Agent系统
"""

from main_agent import InteractiveAgent


def example_usage():
    """
    展示Agent系统的使用方法
    """
    print("=" * 60)
    print("交互式智能Agent系统使用示例")
    print("=" * 60)
    
    # 创建Agent实例
    agent = InteractiveAgent()
    print("✓ 创建Agent实例")
    
    print("\n系统特性:")
    print("• 模块化设计，各组件职责分离")
    print("• 基于状态机的意图识别（默认闲聊 -> 任务状态切换）")
    print("• 用户身份管理和个性化服务")
    print("• 多模态交互（音频+视觉）")
    print("• RAG工具检索与执行")
    
    print("\n" + "-" * 60)
    print("模拟交互流程:")
    print("-" * 60)
    
    # 模拟用户交互序列
    interactions = [
        {
            "description": "用户首次打招呼",
            "input_text": "你好，今天天气真不错！",
            "expected": "闲聊模式响应"
        },
        {
            "description": "用户请求执行任务",
            "input_text": "请帮我播放音乐",
            "expected": "切换到任务模式"
        },
        {
            "description": "用户继续闲聊，但系统保持任务状态",
            "input_text": "你觉得这首歌怎么样？",
            "expected": "任务模式响应"
        },
        {
            "description": "用户请求另一项任务",
            "input_text": "帮我调节灯光亮度",
            "expected": "任务模式响应"
        }
    ]
    
    for i, interaction in enumerate(interactions, 1):
        print(f"\n{i}. {interaction['description']}")
        print(f"   输入: '{interaction['input_text']}'")
        print(f"   预期: {interaction['expected']}")
        
        # 模拟语音转文字
        agent._convert_audio_to_text = lambda x, current_text=interaction['input_text']: current_text
        
        # 处理交互
        response = agent.process_interaction(f"audio_sample_{i}", f"image_sample_{i}")
        print(f"   响应: {response}")
        print(f"   当前状态: {agent.intent_classifier.current_state}")
    
    print("\n" + "-" * 60)
    print("状态管理说明:")
    print("- 系统一启动，默认处于闲聊模式")
    print("- 当检测到任务关键词时，自动切换到任务模式")
    print("- 切换到任务模式后，后续交互保持任务状态")
    print("- 支持长期记忆，记录用户偏好和行为模式")
    print("- 用户信息存储在 usr-identity-info/ 目录")
    print("- 工具描述存储在 mcp_tools/ 目录")
    print("-" * 60)
    
    print(f"\n用户 {agent.current_user_id} 的档案已更新")
    print("系统准备就绪，可以开始实际部署！")
    print("=" * 60)


if __name__ == "__main__":
    example_usage()