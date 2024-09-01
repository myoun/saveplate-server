from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from saveplate import database
from saveplate.routers import autocompletion, recipes, user, auth
from saveplate.config import settings
import logging
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        database.initialize(settings.DB_URL, (settings.DB_USER, settings.DB_PW))
        logger.info("Database connection initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {str(e)}")
        raise
    finally:
        try:
            database.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error while closing database connection: {str(e)}")

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    response = await call_next(request)
    return response

app.include_router(autocompletion.router)
app.include_router(recipes.router)
app.include_router(user.router)
app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)
