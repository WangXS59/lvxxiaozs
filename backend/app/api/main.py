"""
旅行小助手 - FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import Base, engine

# 启动时自动建表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="旅行小助手 Backend",
    version="0.1.0",
    description="AI 旅行规划系统后端",
)

# 允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "旅行小助手 API 服务运行中", "version": "0.1.0"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# 注册路由
from app.api.routes import trip, weather, export  # noqa: E402
app.include_router(trip.router)
app.include_router(weather.router)
app.include_router(export.router)
