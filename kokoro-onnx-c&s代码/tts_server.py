import asyncio
import websockets
import json
import numpy as np
import soundfile as sf
import io
import base64
from kokoro import KModel, KPipeline
from pathlib import Path
import logging
import time
import traceback

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 常量配置
REPO_ID = 'hexgrad/Kokoro-82M-v1.1-zh'
SAMPLE_RATE = 24000
VOICE = 'zf_001'
DEVICE = 'cuda'
HOST = '0.0.0.0'
PORT = 8765


class TTSServer:
    def __init__(self):
        logger.info("初始化TTS服务器...")

        # 预加载模型
        self.model = KModel(repo_id=REPO_ID).to(DEVICE).eval()

        # 初始化pipeline
        self.en_pipeline = KPipeline(lang_code='a', repo_id=REPO_ID, model=False)
        self.zh_pipeline = KPipeline(
            lang_code='z',
            repo_id=REPO_ID,
            model=self.model,
            en_callable=self.en_callable
        )

        logger.info("模型加载完成")

    def en_callable(self, text):
        if text == 'Kokoro':
            return 'kˈOkəɹO'
        elif text == 'Sol':
            return 'sˈOl'
        return next(self.en_pipeline(text)).phonemes

    def speed_callable(self, len_ps):
        speed = 0.8
        if len_ps <= 83:
            speed = 1
        elif len_ps < 183:
            speed = 1 - (len_ps - 83) / 500
        return speed * 1.1

    def generate_audio_sync(self, text, voice=VOICE):
        """同步生成音频"""
        try:
            # 生成音频
            generator = self.zh_pipeline(text, voice=voice, speed=self.speed_callable)
            result = next(generator)
            wav = result.audio

            # 确保音频数据是numpy数组
            if not isinstance(wav, np.ndarray):
                wav = np.array(wav)

            # 确保音频数据是一维的
            if wav.ndim > 1:
                wav = wav.flatten()

            # 归一化音频数据到[-1, 1]范围
            if wav.dtype != np.float32:
                wav = wav.astype(np.float32)

            max_val = np.abs(wav).max()
            if max_val > 1.0:
                wav = wav / max_val

            return wav

        except Exception as e:
            logger.error(f"生成音频时出错: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def generate_audio(self, text, voice=VOICE):
        """异步生成音频并返回base64编码的数据"""
        start_time = time.time()

        try:
            # 在线程池中运行同步的音频生成
            loop = asyncio.get_event_loop()
            wav = await loop.run_in_executor(None, self.generate_audio_sync, text, voice)

            # 将音频转换为base64
            buffer = io.BytesIO()
            # 写入WAV格式，确保使用正确的参数
            sf.write(buffer, wav, SAMPLE_RATE, format='WAV', subtype='PCM_16')
            buffer.seek(0)
            audio_bytes = buffer.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

            generation_time = time.time() - start_time
            logger.info(f"音频生成完成，耗时: {generation_time:.3f}秒, 音频长度: {len(wav) / SAMPLE_RATE:.2f}秒")

            return {
                'status': 'success',
                'audio': audio_base64,
                'sample_rate': SAMPLE_RATE,
                'generation_time': generation_time,
                'audio_length': len(wav) / SAMPLE_RATE
            }

        except Exception as e:
            logger.error(f"生成音频时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'status': 'error',
                'message': str(e)
            }

    async def handle_client(self, websocket, path):
        """处理客户端连接"""
        client_address = websocket.remote_address
        logger.info(f"新客户端连接: {client_address}")

        try:
            async for message in websocket:
                try:
                    # 解析请求
                    request = json.loads(message)
                    text = request.get('text', '')
                    voice = request.get('voice', VOICE)
                    request_id = request.get('id', None)

                    logger.info(f"收到请求 - ID: {request_id}, 文本: {text[:50]}...")

                    if not text:
                        await websocket.send(json.dumps({
                            'status': 'error',
                            'message': '文本不能为空',
                            'id': request_id
                        }))
                        continue

                    # 生成音频
                    result = await self.generate_audio(text, voice)
                    result['id'] = request_id

                    # 发送响应
                    response_json = json.dumps(result)
                    await websocket.send(response_json)
                    logger.info(f"响应已发送 - ID: {request_id}, 大小: {len(response_json) / 1024:.2f}KB")

                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析错误: {str(e)}")
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': '无效的JSON格式'
                    }))
                except Exception as e:
                    logger.error(f"处理请求时出错: {str(e)}")
                    logger.error(traceback.format_exc())
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': f'处理请求时出错: {str(e)}'
                    }))

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端断开连接: {client_address}")
        except Exception as e:
            logger.error(f"连接错误: {str(e)}")
            logger.error(traceback.format_exc())

    async def start(self):
        """启动服务器"""
        logger.info(f"TTS服务器启动在 {HOST}:{PORT}")
        async with websockets.serve(
                self.handle_client,
                HOST,
                PORT,
                max_size=10 * 1024 * 1024,  # 10MB
                max_queue=32,
                compression=None  # 禁用压缩以提高性能
        ):
            await asyncio.Future()  # 永久运行


# 主程序
if __name__ == "__main__":
    try:
        server = TTSServer()
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("服务器正在关闭...")
    except Exception as e:
        logger.error(f"服务器错误: {str(e)}")
        logger.error(traceback.format_exc())