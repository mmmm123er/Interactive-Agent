"""
系统配置文件
定义系统参数和配置选项
"""

# 用户数据存储配置
USER_DATA_DIR = "usr-identity-info"

# 多模态模型配置
MULTIMODAL_MODEL_PATH = "multimodal_model/model.pth"  # 假设的模型路径

# 工具目录配置
MCP_TOOLS_DIR = "mcp_tools"

# RAG检索配置
RAG_TOP_K = 5  # 返回最相关的工具数量

# 音频处理配置
AUDIO_SAMPLE_RATE = 16000  # 音频采样率
AUDIO_CHUNK_SIZE = 1024    # 音频块大小

# 会话配置
SESSION_TIMEOUT = 300  # 会话超时时间（秒）

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = "interactive_agent.log"

# 其他配置项
MAX_USER_PREFERENCES = 20    # 最大用户偏好记录数
MAX_BEHAVIOR_PATTERNS = 20   # 最大行为模式记录数