#!/usr/bin/env python3
"""
A script to update the DeepSeek model settings in the configuration.
"""

import os
import sys
import asyncio
import logging

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.db.mongodb import mongodb

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def update_settings():
    """Update DeepSeek settings in the database."""
    try:
        # Connect to MongoDB
        await mongodb.connect_to_mongo()
        
        # Get database
        db = mongodb.db
        
        # Create settings collection if it doesn't exist
        if 'settings' not in await db.list_collection_names():
            logger.info("Creating settings collection")
            await db.create_collection("settings")
        
        settings_collection = db.settings
        
        # Update DeepSeek philosophy model setting
        result = await settings_collection.update_one(
            {"key": "DEEPSEEK_PHILOSOPHY_MODEL"},
            {"$set": {"value": "deepseek-reasoner"}},
            upsert=True
        )
        
        if result.modified_count > 0:
            logger.info("Updated existing DEEPSEEK_PHILOSOPHY_MODEL setting to 'deepseek-reasoner'")
        elif result.upserted_id:
            logger.info("Created new DEEPSEEK_PHILOSOPHY_MODEL setting with value 'deepseek-reasoner'")
        else:
            logger.info("No changes made to DEEPSEEK_PHILOSOPHY_MODEL setting")
        
        # Update DeepSeek model setting (for safety)
        result = await settings_collection.update_one(
            {"key": "DEEPSEEK_MODEL"},
            {"$set": {"value": "deepseek-chat"}},
            upsert=True
        )
        
        if result.modified_count > 0:
            logger.info("Updated existing DEEPSEEK_MODEL setting to 'deepseek-chat'")
        elif result.upserted_id:
            logger.info("Created new DEEPSEEK_MODEL setting with value 'deepseek-chat'")
        else:
            logger.info("No changes made to DEEPSEEK_MODEL setting")
        
        # Update LLM provider setting
        result = await settings_collection.update_one(
            {"key": "LLM_PROVIDER"},
            {"$set": {"value": "deepseek"}},
            upsert=True
        )
        
        if result.modified_count > 0:
            logger.info("Updated existing LLM_PROVIDER setting to 'deepseek'")
        elif result.upserted_id:
            logger.info("Created new LLM_PROVIDER setting with value 'deepseek'")
        else:
            logger.info("No changes made to LLM_PROVIDER setting")
        
        # List all settings in the database
        logger.info("Current settings in database:")
        async for setting in settings_collection.find():
            logger.info(f"{setting['key']} = {setting['value']}")
            
        # Close MongoDB connection
        await mongodb.close_mongo_connection()
            
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        # Make sure to close the connection in case of error
        try:
            await mongodb.close_mongo_connection()
        except:
            pass
        raise

def main():
    """Run the script."""
    logger.info("Updating DeepSeek settings in the database")
    
    # Create a temporary override for the DEEPSEEK_PHILOSOPHY_MODEL setting
    os.environ["DEEPSEEK_PHILOSOPHY_MODEL"] = "deepseek-reasoner"
    
    # Print current settings from settings object
    logger.info(f"Current DeepSeek settings from config:")
    logger.info(f"DEEPSEEK_API_URL: {settings.DEEPSEEK_API_URL}")
    logger.info(f"DEEPSEEK_MODEL: {settings.DEEPSEEK_MODEL}")
    logger.info(f"DEEPSEEK_PHILOSOPHY_MODEL: {settings.DEEPSEEK_PHILOSOPHY_MODEL}")
    logger.info(f"LLM_PROVIDER: {settings.LLM_PROVIDER}")
    
    # Run the async update function
    asyncio.run(update_settings())
    
    # Remind about restart
    print("\n" + "=" * 60)
    print("SETTINGS UPDATE COMPLETED")
    print("=" * 60)
    print("DeepSeek settings have been updated in the database.")
    print("Please restart the application for changes to take effect.")
    print("=" * 60)

if __name__ == "__main__":
    main() 