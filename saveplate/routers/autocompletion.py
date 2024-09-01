from fastapi import APIRouter, HTTPException
from saveplate.database import ManagedTransaction, transactional
from saveplate.util import lru_with_ttl
from typing import Literal
import logging

router = APIRouter()

logger = logging.getLogger(__name__)

AutoCompletionType = Literal["ingredient"] | Literal["sauce"]

@router.get("/autocompletion")
@lru_with_ttl(ttl_seconds=60*10)
@transactional("read")
def autocompletion(tx: ManagedTransaction, type: AutoCompletionType, data: str, limit: int=10) -> list[str]:
    try:
        t = type.capitalize()
        result = tx.run(f'match (n: {t}) where n.name starts with $prefix return n.name as name order by n.popularity desc limit $limit', prefix=data, limit=limit)
        names = result.value(key="name")
        return names
    except Exception as e:
        logger.error(f"Error in autocompletion: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
