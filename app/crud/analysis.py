from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from app.core.config import database_name, analysis_collection_name
from app.models.analysis import AnalysisModel


async def get_one_analysis_by_query(conn: AsyncIOMotorClient, query: Optional[dict]):
    result = await conn[database_name][analysis_collection_name].find_one(query)
    return AnalysisModel(**result) if result else None


async def update_analysis_by_query_with_item(conn: AsyncIOMotorClient, query: Optional[dict], item: Optional[dict]):
    conn[database_name][analysis_collection_name].update_one(query, {'$set': item})
    return True


async def get_analysis_list_by_query(conn: AsyncIOMotorClient, query: Optional[dict]):
    result = conn[database_name][analysis_collection_name].find(query)
    return [AnalysisModel(**x) async for x in result]
