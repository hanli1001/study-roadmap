# Docker 学习笔记

> 2026.07 · 大一暑假 · 第一次容器化部署

---

## 一、Docker 是什么

Docker 把应用和所有依赖打包成"集装箱"，拿到任何服务器都能直接跑。

**类 ��**：搬家打包——衣服、书、餐具全塞一个箱子，搬到新家直接开箱用。

```
本地代码 + 依赖 → Docker 箱子 → 服务器 docker run → 立即可用
```

---

## 二、三个核心概念

| 概念 | 是什么 | 类比 |
|------|--------|------|
| Dockerfile | 施工图纸 | 造集装箱的说明书 |
| Image（镜像） | 造好的箱子（只读） | 按图纸造出的标准箱 |
| Container（容器） | 箱子插电跑起来 | 通上水电的移动房屋 |

流程：**Dockerfile → docker build → Image → docker run → Container**

---

## 三、Dockerfile 逐行解释

```dockerfile
FROM python:3.12-slim
# 以官方 Python 3.12 精简镜像为起点

WORKDIR /app
# 在箱子里建 /app 文件夹

COPY requirements.txt .
# 先复制购物清单（利用 Docker 缓存，改代码不用重装依赖）

RUN pip install --no-cache-dir -r requirements.txt
# 按清单装依赖。--no-cache-dir 省空间

COPY . .
# 复制所有项目文件进箱子

EXPOSE 8000
# 声明用 8000 端口

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
# 启动命令。--host 0.0.0.0 允许外界访问
```

---

## 四、常用命令

| 命令 | 作用 |
|------|------|
| `docker build -t 名字 .` | 按 Dockerfile 造箱子 |
| `docker run -d --name 容器名 -p 外:内 镜像名` | 启动箱子 |
| `docker ps` | 看正在跑的箱子 |
| `docker ps -a` | 看所有箱子 |
| `docker stop 容器名` | 停箱子 |
| `docker rm 容器名` | 删箱子 |
| `docker logs 容器名` | 看日志（查错用） |
| `docker exec -it 容器名 bash` | 进入箱子内部 |

### run 参数速记

| 参数 | 含义 |
|------|------|
| `-d` | 后台运行 |
| `--name xxx` | 起名 |
| `-p 外:内` | 端口映射 |

---

## 五、端口映射 `-p 8009:8000`

```
外界 → 服务器:8009 → Docker 转接 → 箱子内:8000
```

外端口能换（避开已占用的），内端口必须和 CMD 里的一致。

---

## 六、踩坑记录

| 坑 | 原因 | 解决 |
|----|------|------|
| 中文注释报 unknown instruction | Docker 不支持中文注释 | 纯英文 |
| 长行被终端折断 | SSH 有行宽限制 | 本地写好推 GitHub |
| 外网访问不了 | 防火墙未放行 | `sudo ufw allow 端口` |
| 容器能启动但 404 | `--host` 设成 `127.0.0.1` | 必须 `0.0.0.0` |

---

## 七、部署流程

```
本地写 Dockerfile → git push → SSH 登录服务器 → git pull
→ docker build -t xxx . → docker run -d --name xxx -p 外:内 xxx
→ curl localhost 验证 → 公网访问
```

---

*代码：`Dockerfile` + `requirements.txt` · 服务器路径：`/home/ubuntu/study-roadmap`*
