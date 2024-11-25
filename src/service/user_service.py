from src.database.mongodb import db as mongo_db

async def get_user_preferences_from_base(user_id):
    user_preferences = mongo_db["user_preferences"].find({"id": user_id})
    result = {"genre": [], "category": []}
    async for user_preference in user_preferences:
        if "genre" in user_preference and user_preference["genre"]:
            result["genre"].extend(user_preference["genre"])
        if "category" in user_preference and user_preference["category"]:
            result["category"].extend(user_preference["category"])
    return result


async def get_user_recommendations_from_base(user_id):
    user_recommendations = mongo_db["user_recommendations"].find({"user_id": user_id})
    result = set()
    async for user_recommendation in user_recommendations:
        for hit in user_recommendation["hits"]:
            result.add(hit)
    return result