"""
Paper Agent - 企业级文献管理系统
完整后端实现
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Paper Agent",
    description="企业级AI文献管理系统 - 支持集群部署",
    version="2.0.0",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入并注册路由
try:
    from paper_agent.backend.api.routes import (
        documents, search, summary, users, knowledge, 
        review, arxiv, notebooks, discovery, zotero, drafting
    )
    app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
    app.include_router(search.router, prefix="/api/search", tags=["search"])
    app.include_router(summary.router, prefix="/api/summary", tags=["summary"])
    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge-graph"])
    app.include_router(review.router, prefix="/api/review", tags=["paper-review"])
    app.include_router(arxiv.router, prefix="/api/arxiv", tags=["arxiv"])
    app.include_router(notebooks.router, prefix="/api/notebooks", tags=["notebooks"])
    app.include_router(discovery.router, prefix="/api/discovery", tags=["discovery"])
    app.include_router(zotero.router, prefix="/api/zotero", tags=["zotero"])
    app.include_router(drafting.router, prefix="/api/drafting", tags=["drafting"])
    logger.info("✓ 所有路由已加载（含Research Mentor）")
except Exception as e:
    logger.warning(f"部分路由加载失败: {e}")

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

# 根路径
@app.get("/")
async def root():
    return {
        "name": "Paper Agent API",
        "version": "2.0.0",
        "cluster_enabled": True,
        "features": [
            "集群部署支持",
            "多LLM提供商",
            "知识图谱可视化",
            "论文评审AI",
            "PDF在线阅读",
            "用户多租户系统"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
