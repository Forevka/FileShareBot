import asyncio
import asyncpg

async def insert_file_id(file_name, file_id, owner_id):
    conn = await asyncpg.connect(user='postgres', password='werdwerd',
                                 database='files', host='194.67.205.185')
    values = await conn.fetch('''INSERT INTO all_files(file_name, file_id, owner_id, create_date) VALUES('{}', '{}', {}, current_timestamp)'''.format(file_name, file_id, owner_id))
    await conn.close()

async def find_file_by_name(file_name, offset = 0):
    conn = await asyncpg.connect(user='postgres', password='werdwerd',
                                 database='files', host='194.67.205.185')
    values = await conn.fetch("SELECT file_name, file_id, owner_id, create_date FROM all_files WHERE file_name LIKE '{}%' LIMIT 5 OFFSET {}".format(file_name, offset))
    await conn.close()
    print(values)
    return values;

#loop = asyncio.get_event_loop()
#loop.run_until_complete(find_file_by_name("d"))
