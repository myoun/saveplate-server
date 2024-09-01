from pydantic import BaseModel
from typing import Union, Literal

class AvailableRecipeRequest(BaseModel):
    ingredients: list[str]
    sauces: list[str]

class IngredientEntry(BaseModel):
    name: str
    amount: int

class AddUserIngredient(BaseModel):
    user_email: str
    ingredients: list[IngredientEntry]

