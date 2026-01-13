# 📔 Work Diary Docker

一个基于 Docker 的全栈工作日记应用，支持日记管理、打卡记录和 AI 文本润色功能。

## ✨ 特性

- 📝 **日记管理** - 记录和查看工作日记，自动添加每日一句
- ⏰ **打卡功能** - 记录每日打卡次数，查看完整打卡历史
- 📋 **打卡历史** - 按日期分组显示历史打卡记录，支持分页查询
- 🤖 **AI 润色** - 使用 Groq API (Llama 3.3) 自动润色日记内容
- 🐳 **Docker 部署** - 一键启动，开箱即用
- 🔒 **HTTPS 支持** - 支持 SSL/TLS 加密通信
- 💾 **数据持久化** - MySQL 和 Redis 数据持久化存储

## 🏗️ 技术架构

```
┌─────────────┐
│   用户请求   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│          Nginx (反向代理)            │
│  - 端口: 80/443                      │
│  - SSL/TLS 支持                      │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│       Flask App (Python 后端)        │
│  - REST API                          │
│  - 业务逻辑                           │
│  - AI 集成                           │
└────┬──────────┬──────────────────────┘
     │          │
     ▼          ▼
┌─────────┐  ┌──────────┐
│  MySQL  │  │  Redis   │
│  数据库  │  │  缓存    │
└─────────┘  └──────────┘
```

## 🛠️ 技术栈

### 后端
- **Flask** - Python Web 框架
- **Flask-SQLAlchemy** - ORM 数据库操作
- **PyMySQL** - MySQL 数据库驱动
- **Redis-py** - Redis 客户端
- **Groq SDK** - AI API 集成

### 数据库
- **MariaDB 10.6** - 主数据库，存储日记内容
- **Redis Alpine** - 缓存数据库，存储打卡记录

### 前端服务
- **Nginx** - 反向代理和静态文件服务

### 容器化
- **Docker** - 容器运行时
- **Docker Compose** - 多容器编排

## 🚀 快速开始

### 前置要求

- Docker >= 20.10
- Docker Compose >= 2.0
- Git

### 1. 克隆项目

```bash
git clone https://github.com/pinna901/work-diary-docker.git
cd work-diary-docker
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填写必需的配置
nano .env
```

**必需配置项：**
- `MYSQL_ROOT_PASSWORD` - MySQL 数据库密码
- `GROQ_API_KEY` - Groq AI API 密钥（[获取地址](https://console.groq.com/keys)）

### 3. 生成 SSL 证书（可选）

**开发环境（自签名证书）：**

```bash
# 创建证书目录
mkdir -p certs

# 生成自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/server.key -out certs/server.crt \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=Dev/CN=localhost"
```

**生产环境：**

推荐使用 [Let's Encrypt](https://letsencrypt.org/) 获取免费的有效证书：

```bash
# 使用 certbot
sudo certbot certonly --standalone -d yourdomain.com

# 复制证书到项目目录
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem certs/server.crt
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem certs/server.key
```

### 4. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 等待所有服务健康检查通过
docker-compose ps
```

### 5. 验证部署

访问以下地址验证服务是否正常：

- HTTP: `http://localhost`
- HTTPS: `https://localhost`
- API 状态: `http://localhost/api/status`

## 📚 API 文档

### 1. 健康检查

**端点：** `GET /health`

**描述：** 用于容器健康检查

**响应示例：**

```json
{
  "status": "healthy"
}
```

**curl 示例：**

```bash
curl http://localhost/health
```

---

### 2. 服务状态

**端点：** `GET /api/status`

**描述：** 获取服务状态和打卡统计

**响应示例：**

```json
{
  "status": "online",
  "db": "MySQL",
  "count": 42,
  "ai_enabled": true
}
```

**curl 示例：**

```bash
curl http://localhost/api/status
```

---

### 3. 打卡

**端点：** `POST /api/clock-in` 或 `GET /api/clock-in`

**描述：** 记录打卡，计数器自增

**响应示例：**

```json
{
  "message": "Clock in success!",
  "count": 43
}
```

**curl 示例：**

```bash
# POST 方式
curl -X POST http://localhost/api/clock-in

# GET 方式
curl http://localhost/api/clock-in
```

---

### 4. 添加日记

**端点：** `POST /api/diary`

**描述：** 创建新的日记条目

**请求体：**

```json
{
  "content": "今天完成了 Docker 部署优化，移除了硬编码路径"
}
```

**响应示例：**

```json
{
  "message": "Saved to MySQL!",
  "entry": {
    "id": 1,
    "content": "今天完成了 Docker 部署优化，移除了硬编码路径",
    "quote": "Life was like a box of chocolate, you never know what you are gonna to get.",
    "time": "2024-01-12 14:30:00"
  }
}
```

**curl 示例：**

```bash
curl -X POST http://localhost/api/diary \
  -H "Content-Type: application/json" \
  -d '{"content": "今天学习了 Docker Compose"}'
```

---

### 5. 查看日记列表

**端点：** `GET /api/diary`

**描述：** 获取所有日记，支持分页

**查询参数：**
- `page` - 页码（默认 1）
- `per_page` - 每页条数（默认 10，最大 100）

**响应示例：**

```json
{
  "total": 25,
  "page": 1,
  "per_page": 10,
  "total_pages": 3,
  "diaries": [
    {
      "id": 25,
      "content": "今天的工作内容...",
      "quote": "Stay hungry, stay foolish. —— Steve Jobs",
      "time": "2024-01-12 14:30:00"
    }
  ]
}
```

**curl 示例：**

```bash
# 获取第一页（默认 10 条）
curl http://localhost/api/diary

# 获取第 2 页，每页 20 条
curl "http://localhost/api/diary?page=2&per_page=20"
```

---

### 6. AI 文本润色

**端点：** `POST /api/ai-polish`

**描述：** 使用 AI 对日记内容进行润色

**请求体：**

```json
{
  "content": "今天写了代码"
}
```

**响应示例：**

```json
{
  "result": "今天专注于代码开发，不断精进技术能力，为项目贡献价值。保持热情，持续进步！"
}
```

**错误响应（AI 服务不可用）：**

```json
{
  "error": "AI service is currently unavailable"
}
```

**curl 示例：**

```bash
curl -X POST http://localhost/api/ai-polish \
  -H "Content-Type: application/json" \
  -d '{"content": "今天修复了几个 bug"}'
```

---

## ⚙️ 配置说明

### 环境变量

所有环境变量都在 `.env` 文件中配置：

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `MYSQL_ROOT_PASSWORD` | ✅ | - | MySQL root 密码 |
| `MYSQL_DATABASE` | ✅ | `work_diary_db` | 数据库名称 |
| `GROQ_API_KEY` | ✅ | - | Groq AI API 密钥 |
| `MYSQL_DATA_PATH` | ❌ | `./data/mysql` | MySQL 数据存储路径 |
| `REDIS_DATA_PATH` | ❌ | `./data/redis` | Redis 数据存储路径 |
| `HTTPS_PROXY` | ❌ | - | HTTPS 代理地址 |
| `HTTP_PROXY` | ❌ | - | HTTP 代理地址 |
| `FLASK_DEBUG` | ❌ | `0` | Flask 调试模式 (0=关闭, 1=开启) |

### 数据持久化

项目使用 Docker volumes 实现数据持久化：

**默认路径（相对路径）：**
```
./data/
├── mysql/    # MySQL 数据文件
└── redis/    # Redis 持久化文件
```

**自定义路径：**

在 `.env` 文件中设置绝对路径：

```bash
MYSQL_DATA_PATH=/var/lib/work-diary/mysql
REDIS_DATA_PATH=/var/lib/work-diary/redis
```

### 端口映射

| 服务 | 容器端口 | 主机端口 |
|------|----------|----------|
| Nginx | 80 | 80 |
| Nginx (HTTPS) | 443 | 443 |
| Flask | 5000 | - (内部) |
| MySQL | 3306 | - (内部) |
| Redis | 6379 | - (内部) |

## 🔧 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart python-app

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f [service_name]
```

### 数据管理

```bash
# 备份 MySQL 数据
docker exec work-mysql mysqldump -uroot -p${MYSQL_ROOT_PASSWORD} work_diary_db > backup.sql

# 恢复 MySQL 数据
docker exec -i work-mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD} work_diary_db < backup.sql

# 备份 Redis 数据
docker exec work-redis redis-cli BGSAVE
cp ./data/redis/dump.rdb ./backup/dump.rdb

# 进入 MySQL 命令行
docker exec -it work-mysql mysql -uroot -p

# 进入 Redis 命令行
docker exec -it work-redis redis-cli
```

### 开发调试

```bash
# 查看 Python 应用日志
docker-compose logs -f python-app

# 进入 Python 容器
docker exec -it work-python-app /bin/sh

# 重新构建镜像
docker-compose build --no-cache python-app

# 查看容器资源使用
docker stats
```

## 🐛 故障排查

### 1. 数据库连接失败

**症状：** `Database connection failed` 或 `Can't connect to MySQL server`

**排查步骤：**

```bash
# 1. 检查数据库容器是否运行
docker-compose ps db

# 2. 检查数据库健康状态
docker inspect work-mysql | grep -A 10 Health

# 3. 查看数据库日志
docker-compose logs db

# 4. 手动测试连接
docker exec work-mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD} -e "SELECT 1"
```

**常见原因：**
- 数据库容器未完全启动（等待健康检查通过）
- 密码配置错误（检查 `.env` 文件）
- 数据文件权限问题（检查 `data/mysql` 目录权限）

---

### 2. AI 润色功能不可用

**症状：** `AI service is currently unavailable` 或 `503 Service Unavailable`

**排查步骤：**

```bash
# 1. 检查 GROQ_API_KEY 是否配置
docker exec work-python-app env | grep GROQ_API_KEY

# 2. 检查应用日志
docker-compose logs python-app | grep -i groq

# 3. 测试 API 连接（需要在容器内）
docker exec work-python-app python -c "from groq import Groq; print(Groq(api_key='your_key'))"
```

**常见原因：**
- `GROQ_API_KEY` 未配置或无效
- 需要代理访问但未配置 `HTTPS_PROXY`
- API 配额用尽或服务暂时不可用

---

### 3. Redis 连接失败

**症状：** 打卡功能异常或 `Redis connection refused`

**排查步骤：**

```bash
# 1. 检查 Redis 容器状态
docker-compose ps redis

# 2. 测试 Redis 连接
docker exec work-redis redis-cli ping
# 应该返回: PONG

# 3. 查看 Redis 日志
docker-compose logs redis

# 4. 检查 Redis 数据持久化
ls -la ./data/redis/
```

**常见原因：**
- Redis 容器未启动
- 数据目录权限问题
- 磁盘空间不足

---

### 通用调试技巧

```bash
# 查看所有容器状态和健康检查
docker-compose ps

# 查看特定服务的详细日志
docker-compose logs --tail=100 -f python-app

# 检查容器内部进程
docker exec work-python-app ps aux

# 检查网络连接
docker exec work-python-app ping db
docker exec work-python-app ping redis

# 完全重建环境（注意：会删除数据）
docker-compose down -v
docker-compose up -d --build
```

## 📂 项目结构

```
work-diary-docker/
├── .env.example          # 环境变量模板
├── .gitignore            # Git 忽略文件配置
├── docker-compose.yml    # Docker Compose 编排文件
├── README.md             # 项目文档（本文件）
├── certs/                # SSL 证书目录
│   ├── server.crt
│   └── server.key
├── nginx/                # Nginx 配置
│   └── nginx.conf
├── html/                 # 静态前端文件
│   ├── index.html
│   ├── style.css
│   └── script.js
├── python-app/           # Flask 后端应用
│   ├── Dockerfile        # Python 应用镜像
│   ├── requirements.txt  # Python 依赖
│   ├── app.py            # 主应用文件
│   ├── utils.py          # 工具函数
│   └── test_app.py       # 测试文件
├── logs/                 # 日志目录（自动创建）
│   └── python/
│       └── app.log
└── data/                 # 数据持久化目录（自动创建）
    ├── mysql/            # MySQL 数据文件
    └── redis/            # Redis 持久化文件
```

## 📝 开发指南

### 修改后端代码

1. 修改 `python-app/app.py` 或其他 Python 文件
2. 代码会自动同步到容器（通过 volume 挂载）
3. 重启 Python 应用容器：`docker-compose restart python-app`

### 修改前端代码

1. 修改 `html/` 目录下的文件
2. 刷新浏览器即可看到变化（Nginx 自动服务新文件）

### 添加 Python 依赖

1. 编辑 `python-app/requirements.txt`
2. 重新构建镜像：`docker-compose build python-app`
3. 重启服务：`docker-compose up -d python-app`

### 运行测试

```bash
# 进入 Python 容器
docker exec -it work-python-app sh

# 运行测试
pytest test_app.py -v
```

## 🔒 安全建议

1. **生产环境必须修改默认密码**
   - 使用强密码替换 `MYSQL_ROOT_PASSWORD`
   - 定期更换密码

2. **保护 .env 文件**
   - 不要提交 `.env` 到版本控制
   - 限制文件访问权限：`chmod 600 .env`

3. **使用有效的 SSL 证书**
   - 生产环境使用 Let's Encrypt 或商业证书
   - 禁用自签名证书

4. **关闭调试模式**
   - 生产环境设置 `FLASK_DEBUG=0`
   - 避免暴露敏感错误信息

5. **限制网络访问**
   - 使用防火墙限制端口访问
   - 只暴露必要的端口（80, 443）

6. **定期备份数据**
   - 设置自动备份任务
   - 测试备份恢复流程

## 📄 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues: https://github.com/pinna901/work-diary-docker/issues
- Email: [Your Email]

---

**Happy Coding! 🎉**
