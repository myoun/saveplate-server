from fastapi import APIRouter, HTTPException
from saveplate.database import ManagedTransaction, transactional
from saveplate.model import AvailableRecipeRequest
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/recipes/available")
@transactional("read")
def available_recipes(tx: ManagedTransaction, req: AvailableRecipeRequest) -> list[tuple[str, str, float]]:
    try:
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
        values: list[tuple[str, str, float]] = result.values()
        return values
    except Exception as e:
        logger.error(f"Error in available_recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
