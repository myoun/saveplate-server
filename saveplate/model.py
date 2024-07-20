from pydantic import BaseModel

class AvailableRecipeRequest(BaseModel):
    ingredients: list[str]
    sauces: list[str]