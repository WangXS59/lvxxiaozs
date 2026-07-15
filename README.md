# 旅行小助手 (lvxxiaozs)

基于 RAG + LLM 的 AI 旅行行程规划系统。输入目的地、天数、预算与偏好，自动生成带攻略参考、地图导航、每日天气与智能调整的行程方案。

## 技术栈

- **后端**：FastAPI + LangChain + ChromaDB（向量检索）+ SQLite（持久化）+ 阿里云百炼 / 千问（LLM、Embedding、Rerank）+ 高德地图 API
- **前端**：Vue 3 + Vite + Ant Design Vue + 高德地图 JS API

## 目录结构

```
lvxxiaozs/
├── backend/            # FastAPI 后端
│   ├── app/            # 应用代码（config / agents / rag / services / api）
│   ├── data/           # 旅行攻略 Markdown（RAG 语料）
│   └── requirements.txt
└── frontend/           # Vue3 前端
```

## 快速开始

### 1. 后端

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
pip install -r requirements.txt

# 配置密钥：复制示例并填入你自己的 Key
cp .env.example .env
# 编辑 backend/.env，填入 LLM_API_KEY 与 AMAP_API_KEY

# 首次运行：将攻略向量化入库（需要联网调用 Embedding）
python -m app.rag.vector_db

# 启动服务
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. 前端

```bash
cd frontend
npm install

# 配置高德 JS Key：复制示例并填入
cp .env.example .env
# 编辑 frontend/.env，填入 VITE_AMAP_JS_KEY

npm run dev
```

浏览器打开 http://127.0.0.1:5173 即可使用。

## 环境变量说明

| 变量 | 位置 | 说明 |
| --- | --- | --- |
| `LLM_API_KEY` | `backend/.env` | 阿里云百炼 / 千问 API Key |
| `AMAP_API_KEY` | `backend/.env` | 高德 Web 服务 Key（坐标/天气补全） |
| `VITE_AMAP_JS_KEY` | `frontend/.env` | 高德 JS API Key（地图展示） |

> ⚠️ 所有 `.env` 文件均已写入 `.gitignore`，**不会提交到仓库**。请自行保管密钥。

## 主要功能

- 🔍 RAG 攻略检索（Query Rewrite + Rerank + 噪声过滤）
- 🗺️ 行程生成（景点 / 餐饮 / 住宿 / 预算）
- 🗺️ 高德地图路线导航 + 每日住宿推荐
- 🌤️ 每日天气展示
- 🤖 智能调整（自然语言修改某一天行程，如「把下午换成逛古城，午餐吃米线」）
- 📄 导出 Markdown / PDF
