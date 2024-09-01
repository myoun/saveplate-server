from fastapi import APIRouter, HTTPException
from saveplate.database import ManagedTransaction, transactional
from saveplate.model import AddUserIngredient
from typing import List, Dict, Any
import logging

router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

@router.get("/ingredients")
@transactional("read")
def my_ingredients(tx: ManagedTransaction, user_email: str) -> List[Dict[str, Any]]:
    """
    사용자의 재료 목록을 조회합니다.

    Args:
        user_email (str): 사용자의 이메일 주소

    Returns:
        List[Dict[str, Any]]: 사용자가 가지고 있는 재료 목록
    """
    try:
        result = tx.run("""
            match (u: User) -[:HAS]-> (i) where u.email=$user_email return i
        """, user_email=user_email)

        values = result.values()

        r = []
        for e in values:
            r.append(e[0])

        return r
    except Exception as e:
        logger.error(f"Error in my_ingredients: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/ingredient")
@transactional("write")
def add_ingredient(tx: ManagedTransaction, req: AddUserIngredient) -> List[Any]:
    """
    사용자의 재료를 추가합니다.

    Args:
        req (AddUserIngredient): 사용자 이메일과 추가할 재료 목록

    Returns:
        List[Any]: 추가된 사용자와 재료 정보
    """
    try:
        user_email = req.user_email
        ingredients = req.ingredients
        user_result = tx.run("""
            unwind $ingredients as e
            match (u: User), (i)
            where u.email = $user_email and i.name = e.name
            merge p=(u)-[:Has{amount: e.amount}]->(i)
            return u, i
        """, user_email=user_email, ingredients=ingredients)
        return user_result.values()
    except Exception as e:
        logger.error(f"Error in add_ingredient: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 주석 처리된 쿼리는 함수로 구현하지 않았지만, 필요하다면 다음과 같이 구현할 수 있습니다:
"""
@router.get("/available_recipes")
@transactional("read")
def get_available_recipes(tx: ManagedTransaction, user_email: str) -> List[Dict[str, Any]]:
    try:
        result = tx.run('''
        with $user_email as useremail
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
        ''', user_email=user_email)
        return result.data()
    except Exception as e:
        logger.error(f"Error in get_available_recipes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
"""
