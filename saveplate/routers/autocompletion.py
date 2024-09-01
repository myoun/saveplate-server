from fastapi import APIRouter, HTTPException
from saveplate.database import ManagedTransaction, transactional
from saveplate.util import lru_with_ttl
from typing import Literal
import logging

router = APIRouter(
    prefix="/autocompletion",
    tags=["autocompletion"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

AutoCompletionType = Literal["ingredient"] | Literal["sauce"]

@router.get("")
@lru_with_ttl(ttl_seconds=60*10)
@transactional("read")
def autocompletion(tx: ManagedTransaction, type: AutoCompletionType, data: str, limit: int = 10) -> list[str]:
    """
    재료나 소스 이름의 자동완성 결과를 제공합니다.

    Args:
        type (AutoCompletionType): "ingredient" 또는 "sauce"
        data (str): 검색할 문자열
        limit (int, optional): 반환할 결과의 최대 개수. 기본값은 10.

    Returns:
        list[str]: 자동완성된 이름 목록
    """
    try:
        t = type.capitalize()
        result = tx.run(f'match (n: {t}) where n.name starts with $prefix return n.name as name order by n.popularity desc limit $limit', prefix=data, limit=limit)
        names = result.value(key="name")
        return names
    except Exception as e:
        logger.error(f"Error in autocompletion: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
