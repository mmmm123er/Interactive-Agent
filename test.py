# This file is hardcoded to transparently reproduce HEARME_zh.wav
# Therefore it may NOT generalize gracefully to other texts
# Refer to Usage in README.md for more general usage patterns
import time

# pip install kokoro>=0.8.1 "misaki[zh]>=0.8.1"
from kokoro import KModel, KPipeline
from pathlib import Path
import numpy as np
import soundfile as sf
import tqdm

REPO_ID = 'hexgrad/Kokoro-82M-v1.1-zh'
SAMPLE_RATE = 24000

N_ZEROS = 5000

JOIN_SENTENCES = True

VOICE = 'zf_001'

device = 'cuda'

texts = ["文本转语音（Text-to-Speech，简称TTS）技术允许将电子文本转化为清晰、自然的语音输出。TTS在移动平台的应用不断扩展，主要用于改善用户体验、提供辅助功能以及实现交互式通讯等。",
    "TTS技术通过计算机软件将文本信息转换为听得见的语音信息，广泛应用于智能助手、阅读器和导航系统。它不仅增加了信息获取的渠道，还提升了服务的可达性和包容性。",
    "在移动平台，TTS扮演着至关重要的角色，它使得视障用户能够“听到”屏幕上的内容，同时也为忙碌的3542个用户提供了方便。借助TTS技术，开发者能够构建更加人性化和无障碍的应用。",
    "文本到语音的转换开始于将需要读出的文本准备好。这个文本可以是从用户界面中获取，也可以是从本地或网络资源中读取。接下来，使用TTS对象的 speak 方法将其转换为语音输出。",
    "TTS服务在转换过程中可能会遇到各种异常，如网络问题、语音合成失败、语音引擎不可用等。因此，正确地处理这些异常是必要的。"]


en_pipeline = KPipeline(lang_code='a', repo_id=REPO_ID, model=False)
def en_callable(text):
    if text == 'Kokoro':
        return 'kˈOkəɹO'
    elif text == 'Sol':
        return 'sˈOl'
    return next(en_pipeline(text)).phonemes

def speed_callable(len_ps):
    speed = 0.8
    if len_ps <= 83:
        speed = 1
    elif len_ps < 183:
        speed = 1 - (len_ps - 83) / 500
    return speed * 1.1

model = KModel(repo_id=REPO_ID).to(device).eval()
zh_pipeline = KPipeline(lang_code='z', repo_id=REPO_ID, model=model, en_callable=en_callable)

path = Path(__file__).parent

i = 0
for paragraph in tqdm.tqdm(texts):
    a = time.time()
    print(zh_pipeline.voices.keys())
    generator = zh_pipeline(paragraph, voice=VOICE, speed=speed_callable)
    f = path / f'zh_{i}.wav'
    result = next(generator)
    print(time.time()-a)
    wav = result.audio
    sf.write(f, wav, SAMPLE_RATE)
    i+=1
