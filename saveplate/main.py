from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
from saveplate import database
from saveplate.database import ManagedTransaction, transactional
from saveplate.util import lru_with_ttl
from typing import Literal
from pydantic_settings import BaseSettings
from saveplate.model import AvailableRecipeRequest, AddUserIngredient

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
    return values

@app.get("/user/ingredients")
@transactional("read")
def my_ingredients(tx: ManagedTransaction, user_email: str):
    result = tx.run("""
        match (u: User) -[:HAS]-> (i) where u.email=$user_email return i
    """, user_email=user_email)

    values = result.values()

    r = []
    for e in values:
        r.append(e[0])

    return r

@app.post("/user/ingredient")
@transactional("write")
def add_ingredient(tx: ManagedTransaction, req: AddUserIngredient):
    user_email = req.user_email
    ingredients = req.ingredients
    user_result = tx.run("""
        unwind $ingredients as e
        match (u: User), (i)
        where u.email = $user_email and i.name = e.name
        merge p=(u)-[:Has{amount: e.amount}]->(i)
        return u, i
    """, user_email=user_email, ingrdients=ingredients)
    return user_result.values()

# @app.post("/user/ingredient")
"""
유저 이메일 -> 만들수 있는 레시피 구하기
with "user001@email.com" as useremail
match (u: User) where u.email = useremail
match (u) -[:HAS]-> (i)
where labels(i)[0] in ['Ingredient', 'Sauce']
with collect(i.name) as A
MATCH (i)-[]->(r:Recipe)-[:RECIPE_OF]->(f:Food)
with A, f, r, collect(i.name) as R 
with *, apoc.coll.intersection(A, R) as X
where size(X) <> 0
with *, size(apoc.coll.intersection(X, R)) as i, size(apoc.coll.union(X, R)) as u
where u <> 0
with f.name as food, r.name as recipe, i/toFloat(u) as sim
return food, recipe, sim order by sim desc
"""