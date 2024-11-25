from datetime import datetime
from src.models.program import ProgramWatching
from src.database.mongodb import get_item

async def validate_program_watching_info(program_watching_info: ProgramWatching):
    user = await get_item(program_watching_info.user_id, "users")
    if not user:
        return False, "User with such id doesn't exist."
    program = await get_item(program_watching_info.program_id, "programs")
    if not program:
        return False, "Program with such id doesn't exist."

    try:
        start = datetime.strptime(program_watching_info.start_time, '%Y%m%d%H%M%S %z')
    except ValueError as e:
        return False, str(e)
    try:
        end = datetime.strptime(program_watching_info.end_time, '%Y%m%d%H%M%S %z')
    except ValueError as e:
        return False, str(e)

    if end < start:
        return False, "Дата окончания не может быть раньше даты начала."

    return True, {"start": start, "end": end, "category": program["category"]}
