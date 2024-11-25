import os
import asyncio
from src.celery_app import app as celery_app
from src.database.mongodb import sync_db, upsert_item

from src.tasks.user_recommendations_task import calculate_user_recommendations

MIN_COEFF_TO_ADD_USER_PREFERENCE = float(os.getenv("MIN_COEFF_TO_USER_PREFERENCE"))

@celery_app.task(queue="user_preferences")
def calculate_user_segmentation_by_preferences(user_id=None):
    try:
        if user_id:
            user_programs = list(sync_db["program_watching"].find({"user_id": user_id}))
        else:
            user_programs = list(sync_db["program_watching"].find({}))
        if not user_programs:
            return

        user_counts_by_genre_and_cat = dict()
        for user_program in user_programs:
            user_id = user_program["user_id"]
            day_part = user_program["id"].split('_')[-1]
            category = user_program["category"]
            genre = user_program["genre"]
            day_part_with_category = day_part + '_' + str(category)
            day_part_with_genre = day_part + '_' + genre
            watching_duration = user_program["duration"]

            if user_id not in user_counts_by_genre_and_cat:
                user_counts_by_genre_and_cat[user_id] = {
                    "total_duration": 0,
                    "total_duration_with_category": 0,
                    "genre": {},
                    "category": {},
                }

            user_counts_by_genre_and_cat[user_id]["total_duration"] += watching_duration
            if day_part_with_genre not in user_counts_by_genre_and_cat[user_id]["genre"]:
                user_counts_by_genre_and_cat[user_id]["genre"][day_part_with_genre] = watching_duration
            else:
                user_counts_by_genre_and_cat[user_id]["genre"][day_part_with_genre] += watching_duration

            if category:
                user_counts_by_genre_and_cat[user_id]["total_duration_with_category"] += watching_duration
                if day_part_with_category not in user_counts_by_genre_and_cat[user_id]["category"]:
                    user_counts_by_genre_and_cat[user_id]["category"][day_part_with_category] = watching_duration
                else:
                    user_counts_by_genre_and_cat[user_id]["category"][day_part_with_category] += watching_duration

        for user_id, user_watching in user_counts_by_genre_and_cat.items():
            result = dict()
            total_user_duration = user_counts_by_genre_and_cat[user_id]["total_duration"]
            total_user_duration_with_category = user_counts_by_genre_and_cat[user_id]["total_duration_with_category"]
            genre_preferences = list()
            category_preferences = list()
            top_genre_preference = {}
            top_category_preference = None

            for day_part_with_genre, day_part_with_genre_duration in user_watching["genre"].items():
                if not top_genre_preference:
                    top_genre_preference = (day_part_with_genre, day_part_with_genre_duration)

                if day_part_with_genre_duration > top_genre_preference[1]:
                    top_genre_preference = (day_part_with_genre, day_part_with_genre_duration)

                if day_part_with_genre_duration / total_user_duration >= MIN_COEFF_TO_ADD_USER_PREFERENCE:
                    genre_preferences.append({
                        "day_part": day_part_with_genre.split('_')[0],
                        "genre": day_part_with_genre.split('_')[-1],
                    })
            if not genre_preferences and top_genre_preference:
                genre_preferences.append({
                    "day_part": top_genre_preference[0].split('_')[0],
                    "genre": top_genre_preference[0].split('_')[-1],
                })

            for day_part_with_cat, day_part_with_cat_duration in user_watching["category"].items():
                if not top_category_preference:
                    top_category_preference = (day_part_with_cat, day_part_with_cat_duration)

                if day_part_with_cat_duration > top_category_preference[1]:
                    top_category_preference = (day_part_with_cat, day_part_with_cat_duration)

                if day_part_with_cat_duration / total_user_duration_with_category >= MIN_COEFF_TO_ADD_USER_PREFERENCE:
                    category_preferences.append({
                        "day_part": day_part_with_cat.split('_')[0],
                        "category": day_part_with_cat.split('_')[-1],
                    })
            if not category_preferences and top_category_preference:
                category_preferences.append({
                    "day_part": top_category_preference[0].split('_')[0],
                    "genre": top_category_preference[0].split('_')[-1],
                })

            if genre_preferences:
                result["genre"] = genre_preferences
            if category_preferences:
                result["category"] = category_preferences

            if result:
                result['id'] = user_id
                asyncio.get_event_loop().run_until_complete(upsert_item(result, "user_preferences"))
                calculate_user_recommendations.delay(user_id)

    except Exception as e:
        print(f"Ошибка расчета предпочтений пользователей: {str(e)}")