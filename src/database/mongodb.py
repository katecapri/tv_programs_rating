import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from urllib.parse import quote
from uuid import uuid4
from enum import Enum
from bs4 import BeautifulSoup as Soup


class MongoDBConnection(Enum):
    ASYNC = 'async'
    SYNC = 'sync'


def get_client(connection_type: MongoDBConnection):
    url = f"mongodb://{quote(os.getenv('MONGO_DB_USER'))}:{quote(os.getenv('MONGO_DB_PASSWORD'))}@" \
          f"{quote(os.getenv('MONGO_DB_HOST'))}/?authSource=admin"
    if connection_type == MongoDBConnection.ASYNC:
        client = AsyncIOMotorClient(url)
    else:
        client = MongoClient(url)
    return client


mongo_db_client = get_client(MongoDBConnection.ASYNC)
sync_mongo_db_client = get_client(MongoDBConnection.SYNC)


def get_db(connection_type: MongoDBConnection):
    if connection_type == MongoDBConnection.ASYNC:
        return mongo_db_client[os.getenv("MONGO_DB_DB")]
    else:
        return sync_mongo_db_client[os.getenv("MONGO_DB_DB")]


db = get_db(MongoDBConnection.ASYNC)
sync_db = get_db(MongoDBConnection.SYNC)


async def get_item(item_id: int | str, collection) -> dict | None:
    try:
        result = await db[collection].find_one({"id": item_id})
        if result is None:
            return None
        return result
    except Exception as e:
        print(e)
        return None


async def inset_item(item: dict, collection) -> str:
    existing_item = await db[collection].find_one({"id": item['id']})
    if existing_item:
        print(f"Объект уже существует {item}")
    try:
        result = await db[collection].insert_one(item)
        if result.inserted_id:
            return str(result.inserted_id)
        else:
            print(f"Ошибка вставки объекта {item}")
    except Exception as e:
        print(f"Ошибка вставки объекта {item}: {str(e)}")


async def update_item(item: dict, collection: str) -> dict:
    try:
        result = await db[collection].find_one_and_replace(
            filter={"id": item['id']},
            replacement=item,
            return_document=True
        )
        if result is None:
            print(f"Ошибка при обновлении документа {item['id']}, документ не найден")
        return result
    except Exception as e:
        print(f"Ошибка при обновлении документа {item}: {str(e)}")


async def upsert_item(item, collection: str) -> dict:
    try:
        item_id = item['id']
        result = await db[collection].replace_one(
            filter={"id": item_id},
            replacement=item,
            upsert=True
        )
        if result.upserted_id is not None:
            print(f"Новый документ был создан id {result.upserted_id}")
            return item
        elif result.modified_count > 0:
            print(f"Существующий документ был обновлен id {item_id}")
            return item
        else:
            print(f"Ошибка при вставке/обновлении документа {item}")
    except Exception as e:
        print(f"Ошибка при вставке/обновлении документа {item}: {str(e)}")

async def fill_channels_programs_and_users_collections():
    try:
        if not await db.channels.count_documents({}):
            with open('src/database/programs.xml', 'r', encoding='utf-8') as xml:
                soup = Soup(xml.read(), 'html.parser')
            for channel in soup.find_all('channel'):
                channel_info = {
                    "id": channel.attrs['id'],
                    "name": channel.find('display-name').text
                }
                await inset_item(channel_info, 'channels')
            for program in soup.find_all('programme'):
                program_info = {
                    "id": str(uuid4()),
                    "start": program.attrs['start'],
                    "stop": program.attrs['stop'],
                    "channel": program.attrs['channel'],
                    "name": program.find('title').text,
                    "category": program.find('category').text if program.find('category') else None,
                    "description": program.find('desc').text if program.find('desc') else None
                }
                await inset_item(program_info, 'programs')
        if not await db.users.count_documents({}):
            with open('src/database/users.xml', 'r', encoding='utf-8') as xml:
                soup = Soup(xml.read(), 'html.parser')
            for user in soup.find_all('user'):
                user_info = {
                    "id": user.attrs['id'],
                    "first_name": user.find('first_name').text,
                    "last_name": user.find('last_name').text,
                    "age": user.find('age').text,
                    "age_range": user.find('age_range').text,
                    "gender": user.find('gender').text,
                }
                await inset_item(user_info, 'users')
    except Exception as e:
        print("Ошибка при загрузке каналов, программ или пользователей из файлов")
