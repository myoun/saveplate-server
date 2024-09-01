from pydantic import BaseModel
from datetime import date

class AvailableRecipeRequest(BaseModel):
    ingredients: list[str]
    sauces: list[str]

class IngredientEntry(BaseModel):
    name: str
    amount: int

class AddUserIngredient(BaseModel):
    ingredients: list[IngredientEntry]

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    gender: str | None = None
    birth_date: date | None = None