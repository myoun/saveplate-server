from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
from saveplate import database
from saveplate.database import ManagedTransaction, transactional
from saveplate.util import lru_with_ttl
from typing import Literal
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str
    DB_USER: str
    DB_PW: str

    class Config:
        env_file = '.env'

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.initialize(settings.DB_URL, (settings.DB_USER, settings.DB_PW))
    yield
    database.close()

app = FastAPI(lifespan=lifespan)

AutoCompletionType = Literal["ingredient"] | Literal["sauce"]

@app.get("/autocompletion")
@lru_with_ttl(ttl_seconds=10)
@transactional("read")
def autocompletion(tx: ManagedTransaction, type: AutoCompletionType, data: str, limit: int=10) -> list[str]:
    """endpoint for autocompletion

    ## Params
    - type: ingredient | sauce (string)
    - data: string
    - limit: int
    """
    t = type.capitalize()
    result = tx.run(f'match (n: {t}) where n.name starts with $prefix return n.name as name order by n.popularity desc limit $limit', prefix=data, limit=limit)
    names = result.value(key="name")
    return names
