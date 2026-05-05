from pydantic import BaseModel


class AKGItem(BaseModel):
    nutrient_code: str
    target_value: float
    unit: str

    model_config = {"from_attributes": True}


class FoodItemOut(BaseModel):
    id: int
    name: str
    source: str
    protein: float
    carbohydrate: float
    fat: float
    fiber: float
    iron: float
    vitamin_a: float

    model_config = {"from_attributes": True}
