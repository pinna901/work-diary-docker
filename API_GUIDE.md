# API 使用指南

## 📌 基础信息

**Base URL**: `http://localhost` 或 `https://localhost`  
**API 版本**: v1

---

## 🔄 API 版本对照

### 新版本 API（推荐使用）

所有新版 API 使用 `/api/v1/` 前缀：

```
POST   /api/v1/diaries        # 创建日记
GET    /api/v1/diaries        # 查询日记列表
GET    /api/v1/diaries/{id}   # 查询单条日记
POST   /api/v1/ai/polish      # AI 文本润色
```

### 旧版本 API（保持兼容）

```
POST   /api/diary             # 创建日记（兼容）
GET    /api/diary             # 查询日记列表（兼容）
POST   /api/ai-polish         # AI 文本润色（兼容）
GET    /api/clock-in          # 打卡（仅旧版）
GET    /api/status            # 服务状态（增强）
```

---

## 📝 API 详细说明

### 1. 创建日记

#### 新版 API（推荐）

```bash
POST /api/v1/diaries
```

**请求示例**：
```bash
curl -X POST http://localhost/api/v1/diaries \
  -H "Content-Type: application/json" \
  -d '{
    "content": "今天完成了代码重构，将单体应用改造为分层架构"
  }'
```

**响应示例**：
```json
{
  "message": "Saved to MySQL!",
  "entry": {
    "id": 1,
    "content": "今天完成了代码重构，将单体应用改造为分层架构",
    "quote": "Stay hungry, stay foolish. —— Steve Jobs",
    "time": "2026-01-12 14:30:00"
  }
}
```

#### 旧版 API（兼容）

```bash
POST /api/diary
```

请求和响应格式与新版相同。

---

### 2. 查询日记列表

#### 新版 API（推荐）

```bash
GET /api/v1/diaries?page=1&per_page=20
```

**参数说明**：
- `page`: 页码（默认：1）
- `per_page`: 每页数量（默认：20，最大：100）

**请求示例**：
```bash
# 获取第一页（默认 20 条）
curl http://localhost/api/v1/diaries

# 获取第 2 页，每页 10 条
curl "http://localhost/api/v1/diaries?page=2&per_page=10"
```

**响应示例**：
```json
{
  "total": 25,
  "page": 1,
  "per_page": 20,
  "pages": 2,
  "diaries": [
    {
      "id": 25,
      "content": "最新的日记内容...",
      "quote": "Stay hungry, stay foolish. —— Steve Jobs",
      "time": "2026-01-12 14:30:00"
    },
    {
      "id": 24,
      "content": "之前的日记内容...",
      "quote": "Life is what happens...",
      "time": "2026-01-11 10:15:00"
    }
  ]
}
```

**性能优势**：
- ✅ 启用 Redis 缓存，缓存时间 5 分钟
- ✅ 第一次查询 10-50ms，缓存命中后 0.1-1ms
- ✅ 减少数据库压力 80%

#### 旧版 API（兼容）

```bash
GET /api/diary?page=1&per_page=20
```

响应格式有细微差异：
- 旧版：`total_pages` 字段
- 新版：`pages` 字段

---

### 3. 查询单条日记

#### 新版 API（仅新版支持）

```bash
GET /api/v1/diaries/{id}
```

**请求示例**：
```bash
curl http://localhost/api/v1/diaries/1
```

**成功响应**：
```json
{
  "id": 1,
  "content": "日记内容...",
  "quote": "Stay hungry, stay foolish. —— Steve Jobs",
  "time": "2026-01-12 14:30:00"
}
```

**失败响应**（404）：
```json
{
  "error": "Diary not found"
}
```

---

### 4. AI 文本润色

#### 新版 API（推荐）

```bash
POST /api/v1/ai/polish
```

**请求示例**：
```bash
curl -X POST http://localhost/api/v1/ai/polish \
  -H "Content-Type: application/json" \
  -d '{
    "content": "今天写了代码"
  }'
```

**成功响应**：
```json
{
  "result": "今天专注于代码开发，不断精进技术能力，为项目贡献价值。保持热情，持续进步！"
}
```

**失败响应**（503）：
```json
{
  "error": "AI service unavailable",
  "message": "GROQ_API_KEY not configured"
}
```

**失败响应**（400）：
```json
{
  "error": "写点东西再让我润色嘛"
}
```

#### 旧版 API（兼容）

```bash
POST /api/ai-polish
```

请求和响应格式与新版相同。

---

### 5. 打卡功能

```bash
GET /api/clock-in
POST /api/clock-in
```

**请求示例**：
```bash
curl http://localhost/api/clock-in
```

**响应示例**：
```json
{
  "message": "Clock in success!",
  "count": 43
}
```

**说明**：
- 支持 GET 和 POST 两种方式
- 计数器存储在 Redis 中
- 每次调用计数器 +1

---

### 6. 服务状态检查

```bash
GET /api/status
```

**请求示例**：
```bash
curl http://localhost/api/status
```

**响应示例**：
```json
{
  "status": "online",
  "database": "connected",
  "cache": {
    "hit_rate": "85.50%",
    "hits": 171,
    "misses": 29,
    "enabled": true
  }
}
```

**字段说明**：
- `status`: 服务状态（online/offline）
- `database`: 数据库连接状态（connected/disconnected）
- `cache.hit_rate`: 缓存命中率
- `cache.hits`: 缓存命中次数
- `cache.misses`: 缓存未命中次数
- `cache.enabled`: 缓存是否启用

---

### 7. 健康检查

```bash
GET /health
```

**请求示例**：
```bash
curl http://localhost/health
```

**响应示例**：
```json
{
  "status": "healthy"
}
```

**说明**：用于 Docker 容器健康检查

---

## 🔧 错误处理

### 通用错误响应格式

```json
{
  "error": "错误描述"
}
```

### HTTP 状态码

| 状态码 | 说明 | 场景 |
|--------|------|------|
| 200 | 成功 | GET 请求成功 |
| 201 | 创建成功 | POST 创建资源成功 |
| 400 | 请求错误 | 参数缺失或格式错误 |
| 404 | 未找到 | 资源不存在 |
| 500 | 服务器错误 | 内部错误 |
| 503 | 服务不可用 | AI 服务或 Redis 不可用 |

---

## 🚀 性能优化建议

### 1. 使用分页查询

```bash
# 推荐：每次查询 20 条
curl "http://localhost/api/v1/diaries?per_page=20"

# 避免：一次查询过多
curl "http://localhost/api/v1/diaries?per_page=1000"  # ❌ 不推荐
```

### 2. 利用缓存

```bash
# 第一次查询会访问数据库（10-50ms）
curl http://localhost/api/v1/diaries

# 5分钟内再次查询，从缓存返回（0.1-1ms）⚡
curl http://localhost/api/v1/diaries
```

### 3. 批量操作建议

如果需要批量创建日记，推荐：
- 使用单次请求，后端批量插入（未实现，可扩展）
- 避免循环调用 API

---

## 🔐 安全建议

### 1. HTTPS

生产环境务必使用 HTTPS：

```bash
# ✅ 推荐
curl https://yourdomain.com/api/v1/diaries

# ❌ 避免
curl http://yourdomain.com/api/v1/diaries
```

### 2. 输入验证

后端已实现输入验证：
- 内容长度限制：1-10000 字符
- 自动过滤空内容

### 3. 速率限制

建议前端实现：
- 防抖（Debounce）
- 节流（Throttle）
- 请求队列

---

## 📊 测试示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost"

# 创建日记
response = requests.post(
    f"{BASE_URL}/api/v1/diaries",
    json={"content": "今天学习了 API 使用"}
)
print(response.json())

# 查询日记列表
response = requests.get(
    f"{BASE_URL}/api/v1/diaries",
    params={"page": 1, "per_page": 10}
)
print(response.json())

# AI 润色
response = requests.post(
    f"{BASE_URL}/api/v1/ai/polish",
    json={"content": "写了代码"}
)
print(response.json())
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost';

// 创建日记
async function createDiary(content) {
  const response = await fetch(`${BASE_URL}/api/v1/diaries`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content }),
  });
  return await response.json();
}

// 查询日记列表
async function getDiaries(page = 1, perPage = 20) {
  const response = await fetch(
    `${BASE_URL}/api/v1/diaries?page=${page}&per_page=${perPage}`
  );
  return await response.json();
}

// AI 润色
async function polishText(content) {
  const response = await fetch(`${BASE_URL}/api/v1/ai/polish`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content }),
  });
  return await response.json();
}
```

---

## 🎯 迁移指南

### 从旧版 API 迁移到新版

#### 步骤 1：替换 URL

```javascript
// 旧版
const url = '/api/diary';

// 新版
const url = '/api/v1/diaries';
```

#### 步骤 2：调整响应字段

```javascript
// 旧版响应
{
  "total_pages": 3  // ❌ 旧字段
}

// 新版响应
{
  "pages": 3  // ✅ 新字段
}
```

#### 步骤 3：测试

使用新版 API 进行测试，确保功能正常。

---

## 📞 支持

### 遇到问题？

1. **检查日志**：`docker-compose logs -f python-app`
2. **查看状态**：访问 `/api/status` 查看服务状态
3. **测试连接**：使用 `curl http://localhost/health`

### 反馈渠道

- GitHub Issues: https://github.com/pinna901/work-diary-docker/issues
- 查看文档：`README.md`、`REFACTORING.md`

---

**更新时间**：2026-01-12  
**API 版本**：v1.0.0
