from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

print("Mongo URL:", settings.MONGODB_URL)

client = AsyncIOMotorClient(settings.MONGODB_URL)

database = client[settings.DATABASE_NAME]