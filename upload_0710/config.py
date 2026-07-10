"""
统一配置模块
所有路径、参数、模型配置集中管理，方便修改
"""
import os

# ======================== 基础路径 ========================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
UTILS_DIR = os.path.join(PROJECT_ROOT, "utils")
MODELS_DIR = os.path.join(UTILS_DIR, "models")

# ======================== 用户数据路径 ========================
VOICEPRINT_DB_DIR = os.path.join(DATA_DIR, "Authorized_User_Voiceprint_Database")
USER_CONFIG_DIR = os.path.join(DATA_DIR, "Authorized_User_Config")
COMMAND_FILE_PATH = os.path.join(PROJECT_ROOT, "command.txt")

# ======================== 模型路径 ========================
CAMPPLUS_MODEL_PATH = os.path.join(MODELS_DIR, "campplus")
ASR_MODEL_PATH = os.path.join(MODELS_DIR, "Qwen3-ASR-0.6B")
TTS_MODEL_PATH = os.path.join(MODELS_DIR, "Qwen3-TTS-12Hz-0.6B-CustomVoice")

# ======================== 向量化模型路径 ========================
EMBEDDING_MODEL_NAME = os.path.join(MODELS_DIR, "Qwen3-Embedding-0.6B")
EMBEDDING_CACHE_PATH = os.path.join(DATA_DIR, "command_embeddings.pkl")

# ======================== LLM API 配置 ========================
LLM_API_KEY = "sk-ws-H.EMIRERR.bA5w.MEQCIDvj39oMBiqg18GVQixR1NIhAdjexgCs1JWCFmTqjy3VAiBI0B0YmZn77q_fOHIlGF3cGxqAbZqZbctO_cYGyGzm0A"
LLM_BASE_URL = "https://llm-ip9z9mhyy19015m0.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
LLM_MODEL_NAME = "qwen3.6-flash"
LLM_MAX_TOKENS = 2048
LLM_TEMPERATURE = 0.7
LLM_TOP_P = 0.95

# ======================== 音频参数 ========================
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
SILENCE_TIMEOUT = 1.5
SILENCE_THRESHOLD = 5

# ======================== 摄像头参数 ========================
CAMERA_INDEX = 0
CAMERA_WARMUP_FRAMES = 5

# ======================== 目标检测参数 ========================
YOLO_MODEL_PATH = os.path.join(UTILS_DIR, "yolov8n.pt")
YOLO_DEVICE = "cpu"
YOLO_CONFIDENCE_THRESHOLD = 0.5

# ======================== 临时文件路径 ========================
TEMP_DIR = os.path.join(DATA_DIR, "temp")
TEMP_AUDIO_PATH = os.path.join(TEMP_DIR, "live_audio.wav")
TEMP_IMAGE_PATH = os.path.join(TEMP_DIR, "live_image.jpg")
TEMP_TTS_OUTPUT_PATH = os.path.join(TEMP_DIR, "tts_response.wav")

# ======================== 唤醒词参数 ========================
WAKE_WORDS = ["哈喽", "哈楼", "哈咯", "halou", "ha lou", "hello"]
WAKE_SEGMENT_DURATION = 2.0
WAKE_MIN_VOICE_FRAMES = 5
WAKE_VOICE_RATIO_THRESHOLD = 0.15
TEMP_WAKE_AUDIO_PATH = os.path.join(TEMP_DIR, "wake_audio.wav")

# ======================== 声纹识别参数 ========================
VOICEPRINT_THRESHOLD = 0.31

# ======================== 意图分类参数 ========================
INTENT_SIMILARITY_THRESHOLD = 0.65

# ======================== TTS 参数 ========================
TTS_SERVER_URL = "http://localhost:8000/tts_stream"
TTS_DEVICE = "cpu"
TTS_SPEAKER = "Vivian"
TTS_LANGUAGE = "Chinese"
TTS_SAMPLE_RATE = 24000

# ======================== ASR 参数 ========================
ASR_DEVICE = "cpu"
ASR_MAX_BATCH_SIZE = 32
ASR_MAX_NEW_TOKENS = 256

# ======================== 记忆系统参数 ========================
MEMORY_MAX_TURNS = 20
MEMORY_SUMMARY_THRESHOLD = 10

# ======================== 响应精简参数 ========================
RESPONSE_MAX_LENGTH = 150

# ======================== 能力分类定义 ========================
CAPABILITY_TYPES = {
    "状态查询": {
        "description": "读取机器人状态、任务状态、传感器、地图、定位等信息",
        "tools": [
            {"name": "get_robot_status", "description": "读取机器人本机状态、任务状态和运行健康"},
            {"name": "get_task_info", "description": "读取当前活跃任务、任务栈和待确认项"},
            {"name": "get_map_info", "description": "读取地图就绪状态、坐标系、版本"},
            {"name": "get_localization", "description": "读取定位就绪状态和重定位置信度"},
            {"name": "get_sensor_status", "description": "读取传感器流、帧率、延迟和可用性"},
            {"name": "get_planner_status", "description": "读取全局/局部规划就绪状态"},
            {"name": "get_mcp_capabilities", "description": "读取MCP能力目录和边界"},
        ]
    },
    "空间记忆与场景理解": {
        "description": "查询语义路点、探索摘要、场景状态、语义记忆等",
        "tools": [
            {"name": "query_semantic_waypoint", "description": "根据自然语言目标查询语义路点候选"},
            {"name": "get_exploration_summary", "description": "查询探索会话、路点数量、标签等摘要"},
            {"name": "get_scene_state", "description": "获取当前场景采样状态和可用相机证据"},
            {"name": "get_panoramic_observation", "description": "请求当前位置360度语义观测"},
            {"name": "write_semantic_memory", "description": "请求带溯源的语义记忆写入"},
        ]
    },
    "探索能力": {
        "description": "自主探索、建图、增量搜索等",
        "tools": [
            {"name": "start_exploration", "description": "请求自主探索或建图"},
            {"name": "stop_exploration", "description": "请求停止探索"},
            {"name": "incremental_search", "description": "在探索过程中增量搜索缺失语义目标"},
        ]
    },
    "导航与局部运动能力": {
        "description": "短距离运动、导航到目标点、路径跟随、速度调整等",
        "tools": [
            {"name": "relative_move", "description": "短距离相对运动，如前进三米"},
            {"name": "navigate_to_pose", "description": "导航到指定地图位姿"},
            {"name": "navigate_to_waypoint", "description": "导航到语义路点候选"},
            {"name": "follow_path", "description": "跟随已规划路径"},
            {"name": "adjust_speed", "description": "调整局部规划器速度偏好"},
        ]
    },
    "任务控制能力": {
        "description": "确认、暂停、恢复、取消任务等",
        "tools": [
            {"name": "confirm_task", "description": "确认待确认任务或探索决策"},
            {"name": "pause_task", "description": "暂停活跃任务并保存上下文"},
            {"name": "resume_task", "description": "恢复暂停的任务"},
            {"name": "cancel_task", "description": "取消活跃任务或请求中的任务"},
            {"name": "emergency_stop", "description": "立即请求审计化停止运动"},
        ]
    }
}

# ======================== 流式处理参数 ========================
STREAMING_ENABLED = True
STREAMING_MAX_TOKENS = 300
STREAMING_SENTENCE_DELIMITERS = {"。", "！", "？", "；", "，", ".", "!", "?", ";", ",", "\n"}

# ======================== 唤醒词优化参数 ========================
WAKE_MAX_DURATION = 5.0
WAKE_SPEECH_END_SILENCE = 0.4
WAKE_MIN_SPEECH_DURATION = 0.2

# ======================== 多进程服务参数 ========================
USE_PROCESS_SERVICES = False

# ======================== 初始化目录 ========================
os.makedirs(VOICEPRINT_DB_DIR, exist_ok=True)
os.makedirs(USER_CONFIG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
