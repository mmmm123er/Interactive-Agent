# 交互式智能Agent系统

这是一个模块化的交互式智能Agent系统，能够通过声纹识别和多模态分析与用户交互，识别用户意图并执行相应任务。

## 系统架构

### 模块组成

1. **用户身份管理模块** (`user_identity_manager.py`)
   - 管理用户信息和行为偏好
   - 自动创建和更新用户档案

2. **声纹识别接口模块** (`voice_recognition_interface.py`)
   - 提供声纹识别功能的封装接口
   - 返回用户ID以进行个性化服务

3. **多模态分析模块** (`multimodal_analyzer.py`)
   - 结合摄像头图像进行用户识别
   - 主动向用户打招呼并提供个性化服务

4. **意图识别模块** (`intent_classifier.py`)
   - 基于状态机的意图识别（默认闲聊 -> 任务状态切换）
   - 使用AI模型进行意图分类（可替换为您自己的大模型）
   - 一旦检测到任务请求，后续交互保持任务状态
   - 提取任务相关的关键信息

5. **RAG工具检索模块** (`rag_tool_retriever.py`)
   - 根据用户意图检索相关的MCP工具
   - 返回最匹配的工具列表

6. **主Agent控制器** (`main_agent.py`)
   - 整合所有模块实现完整交互流程
   - 处理用户输入并生成响应

## 数据存储

- 用户信息存储在 `usr-identity-info/` 目录下，以用户ID命名的MD文件
- MCP工具描述存储在 `mcp_tools/` 目录下
- 多模态模型存储在 `multimodal_model/` 目录下

## 配置文件

- `config.py`: 系统参数和配置选项

## 使用方法

1. 确保已准备好声纹识别和多模态分析模块
2. 将其分别替换 `voice_recognition_interface.py` 和 `multimodal_analyzer.py` 中的模拟实现
3. 集成您的大模型到 `ai_model_interface.py`（参见 `MODEL_INTEGRATION.md`）
4. 在 `mcp_tools/` 目录下放置工具描述文件（JSON格式）
5. 运行主程序：
   ```python
   python main_agent.py
   ```

## 扩展性

系统采用高度模块化设计，每个模块职责单一，便于单独测试和维护。可以根据需要替换或增强任一模块的功能。

## 大模型集成

系统设计为可轻松集成您的大模型。参见 `MODEL_INTEGRATION.md` 了解如何将您的大模型替换当前的模拟实现。