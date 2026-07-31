 # 1. 用官方 Python 3.12 做基础镜像
  FROM python:3.12-slim

  # 2. 设工作目录
  WORKDIR /app

  # 3. 先复制依赖文件（利用 Docker
  缓存，代码改了不用重装依赖）
  COPY requirements.txt .

  # 4. 安装依赖
  RUN pip install --no-cache-dir -r
  requirements.txt

  # 5. 复制所有项目文件进容器
  COPY . .

  # 6. 声明端口
  EXPOSE 8000

  # 7. 启动命令
  CMD ["uvicorn", "api:app", "--host", "0.0.0.0",
  "--port", "8000"]