from fastapi import APIRouter, HTTPException, Depends
from saveplate.database import ManagedTransaction, transactional
from saveplate.model import AddUserIngredient
from saveplate.auth import get_current_active_user, User
from typing import List, Dict, Any
import logging
from datetime import date
import neo4j

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

@router.get("/ingredients")
@transactional("read")
def my_ingredients(
    tx: ManagedTransaction,
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    사용자의 재료 목록을 조회합니다.

    Returns:
        List[Dict[str, Any]]: 사용자가 가지고 있는 재료 목록
    """
    try:
        result = tx.run("""
            MATCH (u:User)-[r:HAS]->(i) WHERE u.email=$user_email RETURN i, r.amount
        """, user_email=current_user.email)

        ingredients = []
        for record in result:
            ingredient = dict(record["i"])
            ingredient["amount"] = record["r.amount"]
            if "birth_date" in ingredient and isinstance(ingredient["birth_date"], neo4j.time.Date):
                ingredient["birth_date"] = date.fromisoformat(str(ingredient["birth_date"]))
            if "join_date" in ingredient and isinstance(ingredient["join_date"], neo4j.time.Date):
                ingredient["join_date"] = date.fromisoformat(str(ingredient["join_date"]))
            ingredients.append(ingredient)

        return ingredients
    except Exception as e:
        logger.error(f"Error in my_ingredients: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/ingredient")
@transactional("write")
def add_ingredient(
    tx: ManagedTransaction,
    req: AddUserIngredient,
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    사용자의 재료를 추가합니다.

    Args:
        req (AddUserIngredient): 추가할 재료 목록

    Returns:
        List[Dict[str, Any]]: 추가된 사용자와 재료 정보
    """
    try:
        ingredients = req.ingredients
        user_result = tx.run("""
            UNWIND $ingredients AS e
            MATCH (u:User {email: $user_email})
            MATCH (i:Ingredient {name: e.name})
            MERGE (u)-[r:HAS]->(i)
            ON CREATE SET r.amount = e.amount
            ON MATCH SET r.amount = r.amount + e.amount
            RETURN u, i, r.amount AS amount
        """, user_email=current_user.email, ingredients=[ing.model_dump() for ing in ingredients])
        
        result = []
        for record in user_result:
            user_data = dict(record["u"])
            ingredient_data = dict(record["i"])
            if "birth_date" in user_data and isinstance(user_data["birth_date"], neo4j.time.Date):
                user_data["birth_date"] = date.fromisoformat(str(user_data["birth_date"]))
            if "join_date" in user_data and isinstance(user_data["join_date"], neo4j.time.Date):
                user_data["join_date"] = date.fromisoformat(str(user_data["join_date"]))
            result.append({
                "user": user_data,
                "ingredient": ingredient_data,
                "amount": record["amount"]
            })

        return result
    except Exception as e:
        logger.error(f"Error in add_ingredient: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 주석 처리된 쿼리는 함수로 구현하지 않았지만, 필요하다면 다음과 같이 구현할 수 있습니다:
@router.get("/recipes")
@transactional("read")
def get_available_recipes(
    tx: ManagedTransaction,
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    try:
        result = tx.run('''
        MATCH (u:User {email: $user_email})-[:HAS]->(i)
        WHERE labels(i)[0] IN ['Ingredient', 'Sauce']
        WITH collect(i.name) AS A
        MATCH (i)-[]->(r:Recipe)-[:RECIPE_OF]->(f:Food)
        WITH A, f, r, collect(i.name) AS R 
        WITH *, apoc.coll.intersection(A, R) AS X
        WHERE size(X) <> 0
        WITH *, size(apoc.coll.intersection(X, R)) AS i, size(apoc.coll.union(X, R)) AS u
        WHERE u <> 0
        WITH f.name AS food, r.name AS recipe, i/toFloat(u) AS sim
        RETURN food, recipe, sim ORDER BY sim DESC
        ''', user_email=current_user.email)
        return result.data()
    except Exception as e:
        logger.error(f"Error in get_available_recipes: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Internal server error")
