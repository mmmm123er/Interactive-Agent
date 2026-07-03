#!/usr/bin/env python
"""
快速启动脚本
用于启动交互式智能Agent系统
"""

from main_agent import InteractiveAgent


def main():
    """
    主函数
    """
    print("🚀 启动交互式智能Agent系统...")
    print()
    
    # 创建Agent实例
    agent = InteractiveAgent()
    print("✅ Agent系统初始化完成")
    
    print()
    print("💡 系统功能说明:")
    print("   • 启动时默认为闲聊模式")
    print("   • 检测到任务请求后切换到任务模式")
    print("   • 任务模式下保持状态，直至会话结束")
    print("   • 自动记录用户偏好和行为模式")
    print()
    
    print("🔧 快速测试 - 模拟交互流程:")
    test_interactions = [
        ("你好，今天天气怎么样？", "sample_audio_1", "sample_image_1"),
        ("请帮我播放音乐", "sample_audio_2", "sample_image_2"),
        ("音量调大一点", "sample_audio_3", "sample_image_3"),
        ("你觉得这首歌如何？", "sample_audio_4", "sample_image_4")
    ]
    
    for i, (text, audio, img) in enumerate(test_interactions, 1):
        print(f"\n{i}. 用户输入: '{text}'")
        
        # 临时替换语音转文字方法
        agent._convert_audio_to_text = lambda x, curr_text=text: curr_text
        
        response = agent.process_interaction(audio, img)
        print(f"   系统响应: {response}")
        print(f"   当前状态: {agent.intent_classifier.current_state}")
    
    print()
    print("🎉 系统测试完成!")
    print()
    print("📝 接下来您可以:")
    print("   1. 集成您的声纹识别模块")
    print("   2. 集成您的多模态模型") 
    print("   3. 集成您的大模型 (参见 MODEL_INTEGRATION.md)")
    print("   4. 添加更多MCP工具描述文件")
    print()


if __name__ == "__main__":
    main()