import os
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "oakcean"

    class Config:
        env_file = ".env"

settings = Settings()

class Database:
    client: AsyncIOMotorClient = None
    db = None

    def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB_NAME]
        print(f"Connected to MongoDB at {settings.MONGO_URI}")

    def close(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    async def get_collection(self, collection_name: str):
        if self.db is None:
            self.connect()
        return self.db[collection_name]

    async def create_indexes(self):
        if self.db is None:
            self.connect()
        
        # Instruments indexes
        instruments = self.db["instruments"]
        await instruments.create_index("ticker", unique=True)
        
        # Bars indexes
        bars = self.db["bars_daily"]
        # _id is already unique by definition, but we want fast lookups by ticker+date
        await bars.create_index([("ticker", 1), ("date", 1)])
        await bars.create_index([("exchange", 1), ("date", 1)])

db = Database()
