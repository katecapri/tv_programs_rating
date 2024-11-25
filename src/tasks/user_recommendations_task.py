import asyncio
from src.celery_app import app as celery_app
from src.database.mongodb import sync_db, upsert_item
from src.database.opensearch import opensearch_client


@celery_app.task(queue="user_recommendations")
def calculate_user_recommendations(user_id=None):
    try:
        if user_id:
            users_preferences = list(sync_db["user_preferences"].find({"user_id": user_id}))
        else:
            users_preferences = list(sync_db["user_preferences"].find({}))
        if not users_preferences:
            return

        # {'id': 'user_id', 'genre': [{"day_part": "night", "genre": "Комедия"},.. ], 'category': [...]} from MongoDB
        for user_preferences in users_preferences:
            user_id = user_preferences["id"]
            user_recommendation = {"user_id": user_id}
            if user_preferences["genre"]:
                for genre_preference in user_preferences["genre"]:
                    day_part = genre_preference["day_part"]
                    genre = genre_preference["genre"]

                    query = {
                        'size': 3,
                        "query": {
                            "query_string": {
                              "query": f"genre: {genre} AND day_part: {day_part} AND program_rating:[1 TO 3]"
                            }
                        }
                    }
                    response = opensearch_client.search(
                        body=query,
                        index='program-popularity-*'
                    )

                    if response['hits']:
                        user_recommendation['id'] = f"{user_id}_{day_part}_genre_{genre}"
                        user_recommendation['hits'] = list()
                        for top_program in response['hits']['hits']:
                            user_recommendation['hits'].append(top_program['_source']['program_id'])
                        asyncio.get_event_loop().run_until_complete(
                            upsert_item(user_recommendation, "user_recommendations"))
            if user_preferences["category"]:
                for category_preference in user_preferences["category"]:
                    day_part = category_preference["day_part"]
                    category = category_preference["category"]

                    query = {
                        'size': 3,
                        "query": {
                            "query_string": {
                              "query": f"category: {category} AND day_part: {day_part} AND program_rating:[1 TO 3]"
                            }
                        }
                    }
                    response = opensearch_client.search(
                        body=query,
                        index='program-popularity-*'
                    )
                    print(response)
                    if response['hits']:
                        user_recommendation['id'] = f"{user_id}_{day_part}_category_{category}"
                        user_recommendation['hits'] = list()
                        for top_program in response['hits']['hits']:
                            user_recommendation['hits'].append(top_program['_source']['program_id'])
                        asyncio.get_event_loop().run_until_complete(
                            upsert_item(user_recommendation, "user_recommendations"))

    except Exception as e:
        print(f"Ошибка расчета рекомендаций для пользователей: {str(e)}")