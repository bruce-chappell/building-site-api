from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from mangum import Mangum

app = FastAPI()
handler = Mangum(app)

@app.get("/")
async def root():
    return {"message": "Hello World asdfasdf"}



# Define a Pydantic model for data validation
class Item(BaseModel):
    name: str = Field(..., example="Item name")
    description: str = Field(None, example="Item description")
    price: float #= Field(..., gt=0, example=10.5)
    tax: float = Field(None, example=1.5)

@app.post("/items/")
async def create_item(item: Item):
    # Validate and process the item
    if item.price < 0:
        raise HTTPException(status_code=400, detail="Price must be greater than zero")
    return {"item": item}

