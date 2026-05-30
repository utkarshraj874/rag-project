# from fastapi import FastAPI
# from motor.motor_asyncio import AsyncIOMotorClient
# from pydantic import BaseModel
# from bson import ObjectId

# app = FastAPI()

# MONGO_URI = "mongodb://localhost:27017"   # or your Atlas URI
# client = AsyncIOMotorClient(MONGO_URI)
# db = client["mydatabase"]

# class User(BaseModel):
#     name: str
#     age: int

# @app.post("/users")
# async def add_user(user: User):
#     result = await db["users"].insert_one(user.dict())
#     return {"inserted_id": str(result.inserted_id), "user": user}

# @app.get("/users")
# async def get_users():
#     users = await db["users"].find().to_list(100)
#     # Convert ObjectId to string for JSON serialization
#     for u in users:
#         u["_id"] = str(u["_id"])
#     return users
