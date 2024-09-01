from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from saveplate import database
from pydantic_settings import BaseSettings
from saveplate.routers import autocompletion, recipes, user
import logging

class Settings(BaseSettings):
    DB_URL: str
    DB_USER: str
    DB_PW: str

    class Config:
        env_file = '.env'

settings = Settings()

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
