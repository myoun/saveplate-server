from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
from saveplate import database
from saveplate.database import ManagedTransaction, transactional
from typing import Literal

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.initialize("",("neo4j",""))
    yield
    database.close()

app = FastAPI(lifespan=lifespan)

AutomCompletionType = Literal["ingredient"] | Literal["sauce"]

@app.get("/autocompletion")
@transactional
def autocompletion(tx: ManagedTransaction, data: str):
    result = tx.run('match (n: Ingredient) where n.name starts with $prefix return n.name as name order by n.popularity desc', prefix=data)
    names = result.value(key="name")
    return names

print(autocompletion.__annotations__)