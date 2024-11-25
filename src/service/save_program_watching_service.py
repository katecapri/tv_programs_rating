from enum import Enum
from datetime import datetime, timedelta
from src.models.program import ProgramWatching
from src.database.mongodb import get_item, inset_item, update_item
from src.tasks.user_preferences_task import calculate_user_segmentation_by_preferences


class DatePart(Enum):
    NIGHT = 'night'  # "00:00:00-05:59:59"
    MORNING = 'morning'  # "06:00:00-11:59:59"
    DAY = 'day'  # "12:00:00-17:59:59"
    EVENING = 'evening'  # "18:00:00-23:59:59"


LAST_MINUTE_FOR_PERIOD = {
    DatePart.NIGHT: {"hour": 5, "minute": 59, "second": 59},
    DatePart.MORNING: {"hour": 11, "minute": 59, "second": 59},
    DatePart.DAY: {"hour": 17, "minute": 59, "second": 59},
    DatePart.EVENING: {"hour": 23, "minute": 59, "second": 59},
}

NEXT_DAY_PART_FOR_PERIOD = {
    DatePart.NIGHT: DatePart.MORNING,
    DatePart.MORNING: DatePart.DAY,
    DatePart.DAY: DatePart.EVENING,
    DatePart.EVENING: DatePart.NIGHT,
}


def get_date_part_by_date(date_time):
    if 0 <= date_time.hour < 6:
        return DatePart.NIGHT
    elif 6 <= date_time.hour < 12:
        return DatePart.MORNING
    elif 12 <= date_time.hour < 18:
        return DatePart.DAY
    else:
        return DatePart.EVENING


def get_last_minute_of_period(start_datetime, start_day_part):
    return start_datetime.replace(hour=LAST_MINUTE_FOR_PERIOD[start_day_part]["hour"],
                                  minute=LAST_MINUTE_FOR_PERIOD[start_day_part]["minute"],
                                  second=LAST_MINUTE_FOR_PERIOD[start_day_part]["second"])


async def save_program_watching_day_period(program_watching_info, start_of_period, end_of_period, day_part, category):
    # Проверяем наличие существуеющего просмотра в базе и обрабатываем временные интервалы - до существуеющего или после
    program_watching_id = f"{program_watching_info.user_id}_{program_watching_info.program_id}_" \
                          f"{start_of_period.strftime('%Y%m%d')}_{day_part.value}"
    existing_program_watching = await get_item(program_watching_id, "program_watching")
    result = {
        "id": program_watching_id,
        "user_id": program_watching_info.user_id,
        "program_id": program_watching_info.program_id,
        "genre": program_watching_info.genre,
        "like": program_watching_info.like,
        "category": category,
    }
    if existing_program_watching:
        existing_start = datetime.strptime(existing_program_watching["start_time"], '%Y%m%d%H%M%S %z')
        existing_end = datetime.strptime(existing_program_watching["end_time"], '%Y%m%d%H%M%S %z')
        if existing_start == start_of_period and existing_end == end_of_period:
            return
        if start_of_period <= existing_start:
            result["start_time"] = start_of_period.strftime('%Y%m%d%H%M%S %z')
            if end_of_period <= existing_start:
                result["end_time"] = existing_end.strftime('%Y%m%d%H%M%S %z')
                result["duration"] = int(existing_program_watching["duration"]) + round(
                    (end_of_period - start_of_period).total_seconds() / 60)
                await update_item(result, "program_watching")  # Новое 11:30-11:40, старое 11:45-11:55
            elif end_of_period <= existing_end:
                result["end_time"] = existing_end.strftime('%Y%m%d%H%M%S %z')
                result["duration"] = round((existing_end - start_of_period).total_seconds() / 60)
                await update_item(result, "program_watching")  # Новое 11:30-11:48, старое 11:45-11:55
            else:  # end_of_period > existing_end
                result["end_time"] = end_of_period.strftime('%Y%m%d%H%M%S %z')
                result["duration"] = round((end_of_period - start_of_period).total_seconds() / 60)
                await update_item(result, "program_watching")  # Новое 11:30-11:58, старое 11:45-11:55
        elif existing_start < start_of_period <= existing_end:
            result["start_time"] = existing_start.strftime('%Y%m%d%H%M%S %z')
            if end_of_period <= existing_end:
                return  # Новое 11:47-11:50, старое 11:45-11:55
            else:   # end_of_period > existing_end
                result["end_time"] = end_of_period.strftime('%Y%m%d%H%M%S %z')
                result["duration"] = round((end_of_period - existing_start).total_seconds() / 60)
                await update_item(result, "program_watching")  # Новое 11:47-11:58, старое 11:45-11:55
        else:   # start_of_period > existing_end
            result["start_time"] = existing_start.strftime('%Y%m%d%H%M%S %z')
            result["end_time"] = end_of_period.strftime('%Y%m%d%H%M%S %z')
            result["duration"] = int(existing_program_watching["duration"]) + round(
                (end_of_period - start_of_period).total_seconds() / 60)
            await update_item(result, "program_watching")  # Новое 11:57-11:58, старое 11:45-11:55
    else:
        result["start_time"] = start_of_period.strftime('%Y%m%d%H%M%S %z')
        result["end_time"] = end_of_period.strftime('%Y%m%d%H%M%S %z')
        result["duration"] = round((end_of_period - start_of_period).total_seconds() / 60)
        await inset_item(result, "program_watching")


async def save_program_watching(program_watching_info: ProgramWatching, dates_and_category: dict):
    # Проверяем принадлежность начала и конца одной части дня. В противном случае разбиваем весь диапазон по частям дня
    start_datetime = dates_and_category["start"]
    end_datetime = dates_and_category["end"]
    category = dates_and_category["category"]
    start_day_part = get_date_part_by_date(start_datetime)
    end_day_part = get_date_part_by_date(end_datetime)
    if start_datetime.date() != end_datetime.date() or start_day_part != end_day_part:
        start_of_period = start_datetime
        day_part = start_day_part
        end_of_period = get_last_minute_of_period(start_datetime, day_part)
        while start_of_period < end_datetime:
            if end_of_period > end_datetime:
                end_of_period = end_datetime
            await save_program_watching_day_period(program_watching_info, start_of_period, end_of_period,
                                                   day_part, category)
            start_of_period = end_of_period + timedelta(seconds=1)
            end_of_period = end_of_period + timedelta(hours=6)
            day_part = NEXT_DAY_PART_FOR_PERIOD[day_part]
    else:
        await save_program_watching_day_period(program_watching_info, start_datetime, end_datetime,
                                               start_day_part, category)
    calculate_user_segmentation_by_preferences.delay(program_watching_info.user_id)
