from neo4j import GraphDatabase, Driver, ManagedTransaction
from typing import Optional, Callable, Concatenate, Literal
from contextlib import contextmanager
import inspect

__driver: Optional[Driver] = None

def initialize(url: str, auth: tuple[str, str]) -> Driver:
    global __driver
    __driver = GraphDatabase.driver(url, auth=auth)
    __driver.verify_connectivity()
    return __driver

def close() -> None:
    global __driver
    if __driver != None:
        __driver.close()
    else:
        raise Exception("Driver is not initialized.")

@contextmanager
def useSession(driver:Driver=None, database:str="neo4j"):
    if driver == None:
        global __driver
        driver = __driver
    with driver.session(database=database) as session:
        yield session

TransactionType = Literal["read"] | Literal["write"]

def transactional(type: TransactionType = "read"):
    match type:
        case "read":
            return transactional_read
        case "write":
            return transactional_write

def transactional_write[**P, R](function: Callable[Concatenate[ManagedTransaction, P], R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return_value: R
        with useSession() as session:
            return_value = session.execute_write(function, *args, **kwargs)
        return return_value
    modified_function_annotation = function.__annotations__
    _k = None
    for (k, v) in modified_function_annotation.items():
        if v == ManagedTransaction:
            _k = k
            break
    if _k != None:
        modified_function_annotation.pop(_k)
    wrapper.__annotations__ = function.__annotations__
    wrapper.__name__ = function.__name__

    original_signature = inspect.signature(function)
    function_parameters = list(map(
        lambda p: inspect.Parameter(p.name, p.kind, annotation=p.annotation, default=p.default),
        list(original_signature.parameters.values())[1:]
    ))
    wrapper.__signature__ = inspect.Signature(
        parameters=function_parameters,
        return_annotation=original_signature.return_annotation
    )
    wrapper.__doc__ = function.__doc__

    return wrapper

def transactional_read[**P, R](function: Callable[Concatenate[ManagedTransaction, P], R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return_value: R
        with useSession() as session:
            return_value = session.execute_read(function, *args, **kwargs)
        return return_value
    modified_function_annotation = function.__annotations__
    _k = None
    for (k, v) in modified_function_annotation.items():
        if v == ManagedTransaction:
            _k = k
            break
    if _k != None:
        modified_function_annotation.pop(_k)
    wrapper.__annotations__ = function.__annotations__
    wrapper.__name__ = function.__name__

    original_signature = inspect.signature(function)
    function_parameters = list(map(
        lambda p: inspect.Parameter(p.name, p.kind, annotation=p.annotation, default=p.default),
        list(original_signature.parameters.values())[1:]
    ))
    wrapper.__signature__ = inspect.Signature(
        parameters=function_parameters,
        return_annotation=original_signature.return_annotation
    )
    wrapper.__doc__ = function.__doc__

    return wrapper