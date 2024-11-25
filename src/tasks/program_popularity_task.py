import json

from src.celery_app import app as celery_app
from src.database.mongodb import sync_db
from src.database.opensearch import opensearch_client


@celery_app.task(queue="program_popularity")
def calculate_program_popularity():
    index_name = "program-popularity-index"
    program_genre_dict = dict()
    try:
        day_part_category_dict = {}  # {"day_Комедия": {"prog1": 2, "prog2": 3}}
        day_part_program_dict = {}  # {"day": {"prog1": 2, "prog2": 3}}
        user_programs = list(sync_db["program_watching"].find({}))
        if not user_programs:
            return
        for user_program in user_programs:
            program_genre_dict[user_program["program_id"]] = user_program["genre"]
            day_part = user_program["id"].split('_')[-1]
            category = user_program["category"]
            day_part_with_category = day_part + '_' + str(category)
            program_id = user_program["program_id"] + '_' + str(category)
            # Заполняем количество просмотров программы в категории по частям дня
            if day_part_with_category not in day_part_category_dict:
                day_part_category_dict[day_part_with_category] = dict()
            if program_id not in day_part_category_dict[day_part_with_category]:
                day_part_category_dict[day_part_with_category][program_id] = 1
            else:
                day_part_category_dict[day_part_with_category][program_id] += 1
            # Заполняем количество просмотров программы по частям дня
            if day_part not in day_part_program_dict:
                day_part_program_dict[day_part] = dict()
            if program_id not in day_part_program_dict[day_part]:
                day_part_program_dict[day_part][program_id] = 1
            else:
                day_part_program_dict[day_part][program_id] += 1

        # Заполняем отсортированный рейтинг программ для каждой части дня по категориям
        result_with_categories = dict()  # {'day_Сериал': {'prog2': {'rating': 1,'count': 3}, 'day_Комедия': {'...}}}
        for day_part_with_category, category_counts in day_part_category_dict.items():
            day_part = day_part_with_category.split('_')[0]
            category = day_part_with_category.split('_')[1]
            sorted_progs_by_cat_list_for_day_part = [(program, program_count) for program, program_count in
                                                    sorted(category_counts.items(), key=lambda item: item[1],
                                                           reverse=True)]
            if day_part not in result_with_categories:
                result_with_categories[day_part] = {category: {}}
            else:
                result_with_categories[day_part][category] = {}
            for rating, prog_cat_count in enumerate(sorted_progs_by_cat_list_for_day_part):
                program = prog_cat_count[0]
                program_count = prog_cat_count[1]
                category = day_part_with_category.split('_')[1]
                result_with_categories[day_part][category][program] = {'rating': rating + 1, 'count': program_count}

        # Заполняем отсортированный рейтинг программ для каждой части дня
        result_programs = dict()  # {'day': {'prog2': {'rating': 1,'count': 3}, 'prog1': {...}}}
        for day_part, program_counts in day_part_program_dict.items():
            sorted_programs_list_for_day_part = [(program, program_count) for program, program_count in
                                                 sorted(program_counts.items(), key=lambda item: item[1], reverse=True)]
            result_programs[day_part] = dict()
            for rating, program_with_count in enumerate(sorted_programs_list_for_day_part):
                program = program_with_count[0]
                program_count = program_with_count[1]
                result_programs[day_part][program] = {'rating': rating + 1, 'count': program_count}

        # Очищаем устаревшую статистику
        opensearch_client.delete_by_query(index="program-popularity-index", body={
            "query": {"range": {"program_rating": {"gt": 0}}}
        })

        # Сохраняем новую статистику
        data = ""
        document_number = 1
        for day_part, day_part_results in result_programs.items():
            for program_category_id, rating_and_count in day_part_results.items():
                program_id = program_category_id.split('_')[0]
                category = program_category_id.split('_')[1]
                data += json.dumps({"index": {"_index": index_name, "_id": document_number}}) + "\n"
                data += json.dumps({
                    "day_part": day_part,
                    "program_id": program_id,
                    "program_rating": rating_and_count["rating"],
                    "program_count": rating_and_count["count"],
                    "category": None if category == "None" else category,
                    "genre": program_genre_dict[program_id],
                    "rating_in_category": result_with_categories[day_part][category][program_category_id]["rating"],
                    "count_in_category": result_with_categories[day_part][category][program_category_id]["count"],
                }) + "\n"
                document_number += 1
        opensearch_client.bulk(data)
    except Exception as e:
        print(f"Ошибка расчета популярности программ: {str(e)}")
