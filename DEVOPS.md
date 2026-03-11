# 🚀 Work Diary Docker — DevOps 文档

本文档阐述 **work-diary-docker** 项目的完整 DevOps 实践，涵盖 CI/CD 流水线、容器化部署、环境管理、监控运维和安全策略。

---

## 目录

1. [DevOps 总体架构](#1-devops-总体架构)
2. [容器化架构](#2-容器化架构)
3. [CI/CD 流水线](#3-cicd-流水线)
4. [环境与配置管理](#4-环境与配置管理)
5. [部署流程](#5-部署流程)
6. [健康检查与监控](#6-健康检查与监控)
7. [日志管理](#7-日志管理)
8. [数据持久化与备份](#8-数据持久化与备份)
9. [安全策略](#9-安全策略)
10. [故障排查](#10-故障排查)
11. [常用运维命令速查](#11-常用运维命令速查)

---

## 1. DevOps 总体架构

```
┌──────────────────────────────────────────────────────────────────┐
│                        开发者工作站                                │
│  ┌─────────────┐    git push    ┌─────────────────────────────┐  │
│  │ 本地开发    │ ─────────────► │  GitHub Repository          │  │
│  │ (代码修改)  │                │  (pinna901/work-diary-docker)│  │
│  └─────────────┘                └──────────────┬──────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                                                  │ 触发 CI/CD
                                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                   GitHub Actions (CI/CD)                          │
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ Pre-cleanup │► │ 代码检出     │► │ 自动化测试 (pytest)    │  │
│  └─────────────┘  └──────────────┘  └───────────┬────────────┘  │
│                                                  │               │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────▼────────────┐  │
│  │ 镜像清理    │◄ │ 服务启动     │◄ │ 停止旧容器             │  │
│  └─────────────┘  └──────────────┘  └────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                                  │ 部署到 Self-Hosted Runner
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                        生产服务器                                  │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   Docker Compose 编排                        │ │
│  │                                                              │ │
│  │  ┌──────────┐   ┌──────────────┐   ┌───────┐  ┌────────┐  │ │
│  │  │  Nginx   │   │  Flask App   │   │ MySQL │  │ Redis  │  │ │
│  │  │ :80/:443 │──►│ python-app   │──►│ :3306 │  │ :6379  │  │ │
│  │  │ 反向代理 │   │ :5000 (内部) │   │ 数据库│  │ 缓存   │  │ │
│  │  └──────────┘   └──────────────┘   └───────┘  └────────┘  │ │
│  │                                                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### DevOps 核心原则

| 原则 | 实践方式 |
|------|----------|
| **持续集成** | 每次 `push` 到 `main` 分支自动触发测试 |
| **持续部署** | 测试通过后自动部署到生产服务器 |
| **基础设施即代码** | `docker-compose.yml` 定义完整服务编排 |
| **不可变基础设施** | 每次部署强制重建容器 (`--force-recreate`) |
| **环境一致性** | 开发/生产使用相同的 Docker 镜像 |
| **零停机部署** | 健康检查确保服务就绪后才切换流量 |

---

## 2. 容器化架构

项目使用 **Docker Compose** 编排 4 个服务，形成一个隔离的内部网络：

### 服务清单

| 服务名 | 镜像 | 对外端口 | 职责 |
|--------|------|----------|------|
| `nginx` | `nginx:latest` | 80, 443 | 反向代理、SSL 终止、静态文件服务 |
| `python-app` | 自构建 (Dockerfile) | 无（内部 5000） | Flask REST API、业务逻辑、AI 集成 |
| `db` | `mariadb:10.6` | 无（内部 3306） | 主数据库（日记数据持久化） |
| `redis` | `redis:alpine` | 无（内部 6379） | 缓存层（打卡计数、日记列表缓存） |

### 服务依赖关系

```
nginx
  └── depends_on: python-app

python-app
  └── depends_on:
        ├── db   (condition: service_healthy)  ← 等待 MySQL 健康检查通过
        └── redis (condition: service_started)
```

> **关键设计**：`python-app` 使用 `service_healthy` 等待数据库就绪，防止应用在数据库初始化完成前启动失败。

### Python 应用镜像构建

`python-app/Dockerfile` 构建步骤：

```dockerfile
FROM python:3.11-slim          # 轻量基础镜像
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt  # 安装依赖（使用国内镜像加速）
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]  # 4 worker 进程
```

> **生产优化**：使用 `gunicorn` 替代 Flask 内置服务器，支持 4 个并发 worker 进程，并发能力显著提升。

### 数据卷挂载

| 挂载项 | 宿主机路径 | 容器路径 | 用途 |
|--------|-----------|----------|------|
| MySQL 数据 | `${MYSQL_DATA_PATH:-./data/mysql}` | `/var/lib/mysql` | 数据库持久化 |
| Redis 数据 | `${REDIS_DATA_PATH:-./data/redis}` | `/data` | 缓存持久化 |
| Nginx 配置 | `./nginx/nginx.conf` | `/etc/nginx/conf.d/default.conf` | 反向代理配置 |
| SSL 证书 | `./certs` | `/etc/nginx/certs` | HTTPS 证书 |
| 静态文件 | `./html` | `/usr/share/nginx/html` | 前端页面 |
| 应用代码 | `./python-app` | `/app` | 代码热更新（开发用） |
| 应用日志 | `./logs/python` | `/app/logs` | 日志持久化 |

### Nginx 反向代理配置

Nginx 承担两个核心职责：

1. **HTTP → HTTPS 强制跳转**（端口 80 → 443）
2. **SSL 终止 + 请求路由**：
   - `/` → 静态前端文件（`html/` 目录）
   - `/api/` → Flask 后端（`python-app:5000`）

```nginx
# HTTP 强制跳转 HTTPS
server {
    listen 80;
    return 301 https://$host$request_uri;
}

# HTTPS 服务
server {
    listen 443 ssl;
    ssl_protocols TLSv1.2 TLSv1.3;  # 仅允许现代 SSL 协议
    ssl_ciphers HIGH:!aNULL:!MD5;

    location /api/ {
        proxy_pass http://python-app:5000;  # 内部网络转发
    }
}
```

---

## 3. CI/CD 流水线

CI/CD 由 **GitHub Actions** 实现，配置文件位于 `.github/workflows/deploy.yml`。

### 触发条件

```yaml
on:
  push:
    branches: [ main ]    # main 分支推送时自动触发
  workflow_dispatch:       # 支持手动触发
```

### 流水线阶段

```
Push to main
     │
     ▼
┌────────────────┐
│ 1. Pre-cleanup │  清理工作目录，确保环境干净
└───────┬────────┘
        ▼
┌────────────────┐
│ 2. Checkout    │  拉取最新代码
└───────┬────────┘
        ▼
┌────────────────┐
│ 3. Unit Tests  │  Docker 构建镜像 → 容器内运行 pytest
└───────┬────────┘   ↑ 测试失败则流水线终止，不进行部署
        ▼
┌────────────────────────┐
│ 4. Stop Old Containers │  停止并删除旧容器 (docker compose down)
└───────┬────────────────┘
        ▼
┌────────────────────────┐
│ 5. Deploy              │  生成 .env → docker compose up -d --build
└───────┬────────────────┘
        ▼
┌────────────────┐
│ 6. Cleanup     │  删除 .env 敏感文件、清理悬空镜像
└────────────────┘
```

### 阶段详解

#### 阶段 3：自动化测试

CI 流水线在独立的 Docker 容器内执行测试，确保测试环境与生产环境一致：

```bash
# 构建测试镜像
docker build -t test-image ./python-app

# 容器内收集测试用例
docker run --rm test-image pytest -q --collect-only

# 执行测试（失败则整个 job 失败，阻断部署）
docker run --rm test-image pytest -q
```

> **测试隔离**：测试在独立容器中运行，不依赖外部数据库，确保测试的可重复性和速度。

#### 阶段 5：部署

部署阶段从 **GitHub Secrets** 读取敏感配置并生成 `.env` 文件：

```bash
echo "MYSQL_ROOT_PASSWORD=$ENV_MYSQL_PASS" > .env
echo "MYSQL_DATABASE=$ENV_DB_NAME"        >> .env
echo "GROQ_API_KEY=$ENV_GROQ_KEY"         >> .env
echo "MYSQL_DATA_PATH=..."                >> .env
echo "REDIS_DATA_PATH=..."                >> .env

docker compose --env-file .env up -d --build --force-recreate
```

> **安全清理**：部署完成后立即删除 `.env` 文件（`rm -f .env`），防止敏感信息留存。

#### 阶段 6：清理

```bash
docker image prune -f  # 删除无标签的悬空镜像，释放磁盘空间
```

### Runner 配置

流水线使用 **Self-Hosted Runner**（自托管运行器），运行在生产服务器上：

```yaml
runs-on: self-hosted
```

**优势**：
- 部署时直接在生产服务器执行，无需额外的远程登录步骤
- 复用服务器上已有的 Docker 缓存，加速构建
- 无需将服务器 SSH 密钥暴露给 GitHub

**网络代理**：Runner 配置了 HTTP 代理，确保在受限网络环境中可以拉取镜像：

```yaml
env:
  http_proxy: http://192.168.171.1:7890
  https_proxy: http://192.168.171.1:7890
```

---

## 4. 环境与配置管理

### GitHub Secrets 配置

以下 Secrets 需要在 GitHub 仓库的 `Settings → Secrets and variables → Actions` 中配置：

| Secret 名称 | 说明 | 示例值 |
|-------------|------|--------|
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码 | `MyStr0ngP@ssw0rd!` |
| `DB_NAME` | 数据库名称 | `work_diary_db` |
| `GROQ_API_KEY` | Groq AI API 密钥 | `gsk_...` |
| `MYSQL_DATA_PATH` | MySQL 数据存储路径 | `/home/pinna/my_prod_data/mysql_data` |
| `REDIS_DATA_PATH` | Redis 数据存储路径 | `/home/pinna/my_prod_data/redis_data` |

### 本地开发环境配置

```bash
# 1. 复制配置模板
cp .env.example .env

# 2. 编辑 .env 填写必要配置
#    必填：MYSQL_ROOT_PASSWORD, GROQ_API_KEY

# 3. 保护 .env 文件权限
chmod 600 .env
```

### 环境变量说明

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `MYSQL_ROOT_PASSWORD` | ✅ | — | MySQL root 密码 |
| `MYSQL_DATABASE` | ✅ | `work_diary_db` | 数据库名 |
| `GROQ_API_KEY` | ✅ | — | Groq AI 服务密钥 |
| `MYSQL_DATA_PATH` | ❌ | `./data/mysql` | MySQL 数据目录 |
| `REDIS_DATA_PATH` | ❌ | `./data/redis` | Redis 数据目录 |
| `HTTPS_PROXY` | ❌ | — | HTTPS 代理（访问外网 API） |
| `HTTP_PROXY` | ❌ | — | HTTP 代理 |
| `FLASK_DEBUG` | ❌ | `0` | Flask 调试模式（生产环境必须为 0） |

---

## 5. 部署流程

### 首次部署（手动）

```bash
# 1. 克隆仓库
git clone https://github.com/pinna901/work-diary-docker.git
cd work-diary-docker

# 2. 配置环境变量
cp .env.example .env
nano .env           # 填写 MYSQL_ROOT_PASSWORD 和 GROQ_API_KEY

# 3. 生成 SSL 证书（开发环境用自签名证书）
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/server.key -out certs/server.crt \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=Dev/CN=localhost"

# 4. 启动所有服务
docker compose up -d --build

# 5. 验证服务状态
docker compose ps
curl http://localhost/health
```

### 代码更新部署（自动）

向 `main` 分支推送代码后，GitHub Actions 自动执行：

```
git add .
git commit -m "feat: 添加新功能"
git push origin main
# → 自动触发 CI/CD 流水线
# → 测试通过后自动部署
```

### 手动触发部署

在 GitHub 仓库页面：`Actions → Docker Auto Deploy → Run workflow`

### 部署验证

```bash
# 检查所有容器运行状态
docker compose ps

# 验证 API 可用性
curl http://localhost/health          # 应返回 {"status": "healthy"}
curl http://localhost/api/status      # 应返回服务状态信息

# 查看应用日志
docker compose logs -f python-app
```

---

## 6. 健康检查与监控

### 容器健康检查配置

| 服务 | 检查命令 | 间隔 | 超时 | 重试次数 |
|------|----------|------|------|----------|
| `db` (MariaDB) | `healthcheck.sh --connect --innodb_initialized` | 10s | 5s | 5 次 |
| `redis` | `redis-cli ping` | 10s | 3s | 3 次 |
| `python-app` | HTTP `/health` 端点 | — | — | — |

### 应用健康检查端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `GET /health` | `GET` | 容器存活检查，返回 `{"status": "healthy"}` |
| `GET /api/status` | `GET` | 服务状态检查，含数据库连接状态和 AI 可用状态 |

```bash
# 快速健康检查
curl http://localhost/health
# 期望响应: {"status": "healthy"}

# 完整服务状态
curl http://localhost/api/status
# 期望响应: {"status": "online", "db": "MySQL", "count": 42, "ai_enabled": true}
```

### 资源监控

```bash
# 实时查看各容器 CPU / 内存 / 网络使用
docker stats

# 查看容器资源限制（如有设置）
docker inspect work-python-app | grep -A 10 HostConfig
```

### 缓存层监控

Redis 缓存层提供内置统计监控：

```bash
# 查看 Redis 信息
docker exec work-redis redis-cli info

# 查看缓存命中统计
docker exec work-redis redis-cli info stats | grep -E "keyspace_hits|keyspace_misses"

# 查看当前缓存键
docker exec work-redis redis-cli keys "*"
```

---

## 7. 日志管理

### 日志架构

```
./logs/
└── python/
    └── app.log      # Flask 应用日志（持久化到宿主机）
```

应用日志通过 Docker Volume 挂载到宿主机 `./logs/python/` 目录，确保容器重启后日志不丢失。

### 查看日志命令

```bash
# 实时跟踪所有服务日志
docker compose logs -f

# 只看 Python 应用日志（最近 100 行）
docker compose logs --tail=100 -f python-app

# 只看 Nginx 访问日志
docker compose logs -f nginx

# 查看数据库日志
docker compose logs -f db

# 查看持久化的应用日志文件
tail -f ./logs/python/app.log
```

### 日志级别

应用日志使用 Python `logging` 模块，默认级别根据 `FLASK_DEBUG` 环境变量决定：

| `FLASK_DEBUG` | 日志级别 |
|---------------|----------|
| `0`（生产） | `INFO` |
| `1`（开发） | `DEBUG` |

---

## 8. 数据持久化与备份

### 数据存储位置

| 数据类型 | 默认路径 | 说明 |
|----------|----------|------|
| MySQL 数据文件 | `./data/mysql/` | 日记内容、打卡记录 |
| Redis 持久化文件 | `./data/redis/dump.rdb` | 打卡计数缓存 |
| 应用日志 | `./logs/python/app.log` | 运行日志 |

Redis 配置了 AOF（Append-Only File）模式，确保数据不因意外重启丢失：

```yaml
redis:
  command: redis-server --appendonly yes
```

### 备份操作

#### MySQL 数据库备份

```bash
# 备份全量数据
docker exec work-mysql \
  mysqldump -uroot -p${MYSQL_ROOT_PASSWORD} work_diary_db > \
  backup_$(date +%Y%m%d_%H%M%S).sql

# 验证备份文件
ls -lh backup_*.sql
```

#### MySQL 数据库恢复

```bash
# 从备份文件恢复
docker exec -i work-mysql \
  mysql -uroot -p${MYSQL_ROOT_PASSWORD} work_diary_db < backup_20241201_120000.sql
```

#### Redis 数据备份

```bash
# 触发后台持久化
docker exec work-redis redis-cli BGSAVE

# 等待持久化完成
docker exec work-redis redis-cli LASTSAVE

# 复制 RDB 文件
cp ./data/redis/dump.rdb ./backup/redis_$(date +%Y%m%d).rdb
```

### 生产环境备份建议

```bash
# 添加到 crontab 实现每日自动备份
# 每天凌晨 2:00 执行
0 2 * * * docker exec work-mysql mysqldump \
  -uroot -p$MYSQL_ROOT_PASSWORD work_diary_db \
  > /backup/mysql/diary_$(date +\%Y\%m\%d).sql

# 保留最近 30 天的备份
find /backup/mysql/ -name "*.sql" -mtime +30 -delete
```

---

## 9. 安全策略

### 密钥管理

| 实践 | 说明 |
|------|------|
| **GitHub Secrets** | 所有敏感配置通过 GitHub Secrets 注入，不硬编码在代码中 |
| **.env 文件** | 本地开发使用 `.env`，已加入 `.gitignore`，不提交到版本控制 |
| **部署后清理** | CI/CD 部署完成后立即 `rm -f .env`，防止 Runner 上留存敏感文件 |
| **文件权限** | 生产环境执行 `chmod 600 .env` |

### 网络安全

| 实践 | 说明 |
|------|------|
| **端口最小化暴露** | 仅 Nginx 的 80/443 对外，数据库和后端服务不暴露 |
| **HTTPS 强制** | Nginx 将所有 HTTP 请求 301 跳转到 HTTPS |
| **现代 SSL 协议** | 仅允许 TLSv1.2 和 TLSv1.3，禁用不安全的加密套件 |
| **内部网络隔离** | MySQL、Redis、Flask 通过 Docker 内部网络通信，不对外暴露 |

### 应用安全

| 实践 | 说明 |
|------|------|
| **调试模式** | 生产环境强制 `FLASK_DEBUG=0` |
| **密码强度** | MySQL root 密码要求使用强密码 |
| **容器最小权限** | 使用 `python:3.11-slim` 轻量镜像，减少攻击面 |

### SSL 证书管理

```bash
# 生产环境：使用 Let's Encrypt 免费证书
sudo certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem certs/server.crt
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem certs/server.key

# 证书续期（添加到 crontab）
0 12 * * * certbot renew --quiet && \
  cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /path/to/project/certs/server.crt && \
  cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /path/to/project/certs/server.key && \
  docker compose restart nginx
```

---

## 10. 故障排查

### 快速诊断流程

```bash
# 1. 检查所有容器状态
docker compose ps

# 2. 查看有问题的服务日志
docker compose logs --tail=50 [service_name]

# 3. 检查容器内部进程
docker exec [container_name] ps aux

# 4. 检查网络连通性
docker exec work-python-app ping db
docker exec work-python-app ping redis
```

### 常见问题

#### 问题 1：部署后服务不可访问

```bash
# 检查 Nginx 是否启动
docker compose ps nginx

# 检查 80/443 端口占用
sudo netstat -tlnp | grep -E "80|443"

# 查看 Nginx 日志
docker compose logs nginx
```

#### 问题 2：数据库连接失败

```bash
# 检查 MySQL 健康状态
docker inspect work-mysql | grep -A 10 Health

# 手动测试连接
docker exec work-mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD} -e "SELECT 1"

# 常见原因：数据库初始化未完成，等待健康检查通过
docker compose ps db  # 状态应为 healthy
```

#### 问题 3：CI/CD 流水线失败

```bash
# 在 GitHub Actions 页面查看详细日志：
# Repository → Actions → 选择失败的 workflow run → 查看 job 日志

# 常见失败原因：
# - 测试用例失败：检查 "Run Unit Tests" 步骤的 pytest 输出
# - GitHub Secrets 未配置：检查 "Deploy" 步骤是否报 "Secret 为空"
# - Docker 构建失败：检查 Dockerfile 和依赖是否正确
```

#### 问题 4：AI 润色功能不可用

```bash
# 确认 API Key 已配置
docker exec work-python-app env | grep GROQ_API_KEY

# 测试 API 连通性（如需代理）
docker exec work-python-app curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" | head -c 200
```

#### 问题 5：磁盘空间不足

```bash
# 查看 Docker 占用的磁盘空间
docker system df

# 清理停止的容器、悬空镜像和未使用的网络
docker system prune -f

# 清理所有未使用的镜像（谨慎使用）
docker image prune -a -f
```

---

## 11. 常用运维命令速查

### 服务管理

```bash
# 启动所有服务
docker compose up -d

# 停止所有服务（保留数据）
docker compose down

# 停止并删除数据卷（⚠️ 会丢失数据）
docker compose down -v

# 重启单个服务
docker compose restart python-app

# 强制重建并启动
docker compose up -d --build --force-recreate
```

### 日志查看

```bash
# 所有服务实时日志
docker compose logs -f

# 指定服务（最近 100 行）
docker compose logs --tail=100 -f python-app

# 查看持久化日志
tail -f ./logs/python/app.log
```

### 容器调试

```bash
# 进入 Python 应用容器
docker exec -it work-python-app /bin/sh

# 进入 MySQL 命令行
docker exec -it work-mysql mysql -uroot -p

# 进入 Redis 命令行
docker exec -it work-redis redis-cli

# 查看容器资源使用
docker stats --no-stream
```

### 测试执行

```bash
# 在本地容器中运行测试
docker compose exec python-app pytest -v

# 或进入容器后运行
docker exec -it work-python-app sh -c "pytest -v"
```

### 数据操作

```bash
# 备份 MySQL
docker exec work-mysql mysqldump \
  -uroot -p${MYSQL_ROOT_PASSWORD} work_diary_db > backup.sql

# 恢复 MySQL
docker exec -i work-mysql \
  mysql -uroot -p${MYSQL_ROOT_PASSWORD} work_diary_db < backup.sql

# Redis 缓存清空
docker exec work-redis redis-cli FLUSHALL
```

---

## 参考文档

| 文档 | 说明 |
|------|------|
| [README.md](./README.md) | 项目总览、快速开始、配置说明 |
| [API_GUIDE.md](./API_GUIDE.md) | 完整 API 文档与使用示例 |
| [REFACTORING.md](./REFACTORING.md) | 应用架构与重构说明 |
| [SUMMARY.md](./SUMMARY.md) | 重构成果汇总 |
| [docker-compose.yml](./docker-compose.yml) | 服务编排定义 |
| [.github/workflows/deploy.yml](./.github/workflows/deploy.yml) | CI/CD 流水线定义 |

---

*最后更新：2026-03-11*
