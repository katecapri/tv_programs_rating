from pydantic import BaseModel


class GenrePreference(BaseModel):
    day_part: str
    genre: str

class CategoryPreference(BaseModel):
    day_part: str
    category: str

class UserPreferences(BaseModel):
    genre: list[GenrePreference]
    category: list[CategoryPreference]
