# AI 财报异动雷达 API 镜像
# 用法：见 README「Docker 部署」一节（docker compose up -d）
# 注意：data/ 下的 FAISS 索引体积大且是数据，不进镜像，运行时用 volume 挂载
FROM python:3.11-slim

WORKDIR /app

# 先装依赖（利用 Docker 层缓存：requirements 不变则跳过重装）
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 再拷代码（代码变更只重建最后一层）
COPY api_app.py .

EXPOSE 8000

# API_KEY 缺失时 api_app.py 会直接拒绝启动（防裸奔）
CMD ["uvicorn", "api_app:app", "--host", "0.0.0.0", "--port", "8000"]
