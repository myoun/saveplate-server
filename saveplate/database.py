from neo4j import GraphDatabase, Driver, ManagedTransaction, Session
from typing import Optional, Callable, Concatenate, Literal, Generator
from contextlib import contextmanager
from functools import wraps
import inspect
import logging

logger = logging.getLogger(__name__)

__driver: Optional[Driver] = None

def initialize(url: str, auth: tuple[str, str]) -> Driver:
    global __driver
    try:
        __driver = GraphDatabase.driver(url, auth=auth)
        __driver.verify_connectivity()
        logger.info("Database driver initialized successfully")
        return __driver
    except Exception as e:
        logger.error(f"Failed to initialize database driver: {str(e)}")
        raise

def close() -> None:
    global __driver
    if __driver is not None:
        try:
            __driver.close()
            logger.info("Database driver closed successfully")
        except Exception as e:
            logger.error(f"Error while closing database driver: {str(e)}")
            raise
    else:
        logger.warning("Attempted to close uninitialized database driver")
        raise Exception("Driver is not initialized.")

@contextmanager
def useSession(driver: Driver | None = None, database: str = "neo4j") -> Generator[Session, None, None]:
    if driver is None:
        global __driver
        driver = __driver
    with driver.session(database=database) as session:
        yield session

TransactionType = Literal["read"] | Literal["write"]

def transactional(type: TransactionType = "read"):
    def decorator[**P, R](function: Callable[Concatenate[ManagedTransaction, P], R]) -> Callable[P, R]:
        @wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with useSession() as session:
                execute_method = session.execute_write if type == "write" else session.execute_read
                return execute_method(function, *args, **kwargs)
        
        wrapper.__annotations__ = {k: v for k, v in function.__annotations__.items() if v != ManagedTransaction}

        original_sig = inspect.signature(function)
        params = list(original_sig.parameters.values())[1:]  # ManagedTransaction 파라미터 제거
        wrapper.__signature__ = original_sig.replace(parameters=params)

        return wrapper
    return decorator