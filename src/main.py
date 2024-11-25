from typing import List
from fastapi import FastAPI, Response, status
from src.database.mongodb import mongo_db_client, sync_mongo_db_client, fill_channels_programs_and_users_collections
from src.database.opensearch import opensearch_client
from src.models.program import ProgramWatching
from src.models.user import UserPreferences
from src.serializers import validate_program_watching_info
from src.service.save_program_watching_service import save_program_watching
from src.service.user_service import get_user_preferences_from_base, get_user_recommendations_from_base


app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await fill_channels_programs_and_users_collections()


@app.on_event("shutdown")
async def shutdown_event():
    mongo_db_client.close()
    sync_mongo_db_client.close()
    opensearch_client.close()


@app.post("/program_watching")
async def save_program_watching_api(program_watching_info: ProgramWatching, response: Response):
    try:
        # Получаем отметку о корректности данных и либо текст ошибки, либо список из дат в формате datetime
        is_data_valid, error_or_watching_info = await validate_program_watching_info(program_watching_info)
        if not is_data_valid:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"detail": error_or_watching_info}
        await save_program_watching(program_watching_info, error_or_watching_info)
        return {'status': "OK"}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": e}

@app.get("/user_preferences/{user_id}")
async def get_user_preferences(user_id: str, response: Response) -> UserPreferences:
    try:
        user_preferences = await get_user_preferences_from_base(user_id)
        return user_preferences
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": e}

@app.get("/user_recommendations/{user_id}")
async def get_user_recommendations(user_id: str, response: Response) -> List [str]:
    try:
        user_recommendations = await get_user_recommendations_from_base(user_id)
        return user_recommendations
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": e}

