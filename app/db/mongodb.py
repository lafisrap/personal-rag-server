from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    async def connect_to_mongo(self):
        """Create MongoDB connection."""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URI)
            self.db = self.client[settings.MONGODB_DB_NAME]
            # Validate the connection
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB")
        except ConnectionFailure:
            logger.error("Could not connect to MongoDB")
            raise

    async def close_mongo_connection(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Closed connection to MongoDB")

    # Helper functions to get collections
    def get_assistants_collection(self):
        return self.db.assistants

    def get_threads_collection(self):
        return self.db.threads

    def get_messages_collection(self):
        return self.db.messages

    def get_files_collection(self):
        return self.db.files

    def get_categories_collection(self):
        return self.db.categories

    def get_tags_collection(self):
        return self.db.tags


# Create a singleton instance
mongodb = MongoDB()
