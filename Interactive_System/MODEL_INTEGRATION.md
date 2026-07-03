# 大模型集成指南

本文档介绍如何将您现有的大模型集成到Agent系统中。

## 当前实现

目前系统使用模拟的大模型接口 (`ai_model_interface.py`)，其中的 `mock_ai_intent_classification` 函数是模拟实现。

## 集成步骤

### 1. 替换AI模型接口

在 `ai_model_interface.py` 文件中，将 `mock_ai_intent_classification` 函数替换为调用您真实大模型的函数：

```python
def real_ai_intent_classification(text):
    """
    真实AI模型的意图分类功能
    
    Args:
        text (str): 输入文本
        
    Returns:
        dict: 包含意图类型和置信度的结果
    """
    # 调用您的大模型API
    # 示例伪代码：
    # response = your_large_model_api.call(
    #     prompt=f"请分析以下文本的意图类型：'{text}'\n回复格式：{{'intent': 'chat|task', 'confidence': 0.x}}",
    #     max_tokens=100
    # )
    # return response.parsed_result
    
    # 临时保留模拟实现直到您集成真实模型
    pass
```

### 2. 修改AI模型接口类

同样在 `ai_model_interface.py` 中，更新 `AIModelInterface` 类以使用您的大模型：

```python
class AIModelInterface:
    def __init__(self):
        """
        初始化AI模型接口
        连接到您的大模型服务
        """
        # 初始化您的大模型客户端
        # 例如：self.model_client = YourModelClient(api_key="...")
        pass
    
    def classify_intent_with_ai(self, text):
        """
        使用AI模型分类用户意图
        
        Args:
            text (str): 用户输入文本
            
        Returns:
            tuple: (intent_type, confidence_score)
        """
        # 调用真实的大模型
        result = real_ai_intent_classification(text)  # 或者直接调用您的模型
        return result['intent'], result['confidence']
```

### 3. 配置模型参数

在 `config.py` 中添加大模型相关的配置选项：

```python
# 大模型配置
LLM_MODEL_NAME = "your-model-name"  # 您的大模型名称
LLM_TEMPERATURE = 0.3               # 生成温度
LLM_MAX_TOKENS = 100               # 最大token数
LLM_API_KEY = os.getenv("LLM_API_KEY")  # API密钥
LLM_BASE_URL = "https://api.your-llm-provider.com"  # API基础URL
```

### 4. 集成示例

如果您使用的是常见的大模型API（如OpenAI、Anthropic等），可以参考以下集成方式：

#### OpenAI风格API集成示例

```python
import openai

def real_ai_intent_classification(text):
    client = openai.OpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL
    )
    
    prompt = f"""
    分析以下用户输入的意图类型：
    
    用户输入: "{text}"
    
    请判断这是闲聊还是任务请求：
    - 如果是闲聊（如问候、情感表达、社交互动），返回 "chat"
    - 如果是任务请求（如要求执行操作、获取信息、控制设备），返回 "task"
    
    请以JSON格式返回结果：
    {{
        "intent": "chat|task",
        "confidence": 0.x,
        "explanation": "简要说明判断依据"
    }}
    """
    
    response = client.chat.completions.create(
        model=LLM_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=LLM_MAX_TOKENS,
        temperature=LLM_TEMPERATURE
    )
    
    import json
    try:
        result = json.loads(response.choices[0].message.content)
        return result
    except:
        # 如果解析失败，返回默认值
        return {"intent": "chat", "confidence": 0.5, "explanation": "解析失败，返回默认值"}
```

### 5. 测试集成

集成完成后，运行测试验证功能：

```bash
python test_state_machine.py
python example_usage.py
```

## 注意事项

1. **性能考虑**：大模型调用可能较慢，考虑添加缓存或异步处理
2. **错误处理**：确保妥善处理网络错误、API限制等异常情况
3. **成本控制**：监控API使用量以控制费用
4. **隐私保护**：确保用户数据安全，遵循隐私法规

## 扩展功能

您还可以利用大模型的其他能力扩展系统功能：

1. **上下文理解**：分析对话历史以更好地理解用户意图
2. **情感分析**：识别用户情感状态以提供更个性化的响应
3. **实体抽取**：从用户输入中提取关键实体信息
4. **对话管理**：管理复杂的多轮对话流程

完成集成后，系统将能够利用强大的大模型能力来更准确地识别用户意图。