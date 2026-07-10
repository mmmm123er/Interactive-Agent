LOCAL_WORKDIR="/home/GNC618/WokSpace/Interactive_System/utils/models/Qwen3-ASR-0.6B/"
HOST_PORT=8000
CONTAINER_PORT=80
docker run --runtime=nvidia \
    --name qwen3-asr \
    -v /var/run/docker.sock:/var/run/docker.sock -p $HOST_PORT:$CONTAINER_PORT \
    --mount type=bind,source=$LOCAL_WORKDIR,target=/data/shared/Qwen3-ASR \
    --shm-size=4gb \
    -it qwenllm/qwen3-asr:latest