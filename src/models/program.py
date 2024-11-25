from pydantic import BaseModel


class ProgramWatching(BaseModel):
    user_id: str
    program_id: str
    start_time: str
    end_time: str
    genre: str
    like: bool