from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from SERVER.core.config import settings
from SERVER.core.database import init_db, async_session
from SERVER.api.routes import router
from SERVER.services.user_service import create_default_users


@asynccontextmanager
async def lifespan(app: FastAPI):

    await init_db()

    async with async_session() as session:
        await create_default_users(session)
    yield

    pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Agentic AI Command & Control System",
    lifespan=lifespan,
)


cors_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/health",
    }
