from pydantic import BaseModel

class AvailableRecipeRequest(BaseModel):
    ingredients: list[str]
    suaces: list[str]