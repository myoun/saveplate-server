from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
from saveplate import database
from saveplate.database import ManagedTransaction, transactional
from saveplate.util import lru_with_ttl
from typing import Literal
from pydantic_settings import BaseSettings
from saveplate.model import AvailableRecipeRequest

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

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    print(await request.body())
    response = await call_next(request)
    return response

AutoCompletionType = Literal["ingredient"] | Literal["sauce"]

@app.get("/autocompletion")
@lru_with_ttl(ttl_seconds=60*10)
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

@app.post("/recipes/available")
# @lru_with_ttl(ttl_seconds=60*10)
@transactional("read")
def available_recipes(tx: ManagedTransaction, req: AvailableRecipeRequest):
    print(req)
    result = tx.run("""
WITH $ingredients as A
MATCH (i)-[]->(r:Recipe)-[:RECIPE_OF]->(f:Food)
with A, f, r, collect(i.name) as R 
with *, apoc.coll.intersection(A, R) as X
where size(X) <> 0
with *, size(apoc.coll.intersection(X, R)) as i, size(apoc.coll.union(X, R)) as u
where u <> 0
with f.name as food, r.name as recipe, i/toFloat(u) as sim
return food, recipe, sim order by sim desc
""", ingredients=req.ingredients)
    values = result.values()
    print(values)
    return values