import asyncio
import asyncpg

async def insert_file_id(file_name, file_id, owner_id):
    conn = await asyncpg.connect(user='postgres', password='werdwerd',
                                 database='files_new', host='194.67.205.185')
    values = await conn.execute("""INSERT INTO all_files(file_name, file_id, owner_id, create_date) VALUES('{}', '{}', {}, current_timestamp) ON CONFLICT (file_id) DO NOTHING RETURNING 0;""".format(file_name.replace("'","''"), file_id, owner_id))
    if values.split(" ")[-1]=='0':
        await conn.close()
        return 0; #nothing added
    else:
        await conn.execute("""UPDATE users SET files_count = files_count + 1 WHERE user_id = {}""".format(owner_id))
        await conn.close()
        return 1; #added new file id
    
async def file_change_private(file_id, user_id):
    conn = await asyncpg.connect(user='postgres', password='werdwerd',
                                 database='files_new', host='194.67.205.185')
    values = await conn.fetch("""UPDATE all_files SET private = NOT private WHERE (file_id = '{}' AND owner_id = {})""".format(file_id, user_id))
    await conn.close()
    return values;

async def find_file_by_name(file_name, offset = 0):
    conn = await asyncpg.connect(user='postgres', password='werdwerd',
                                 database='files_new', host='194.67.205.185')
    values = await conn.fetch("SELECT file_name, file_id, owner_id, create_date FROM all_files WHERE (LOWER(file_name) LIKE LOWER('{}%') AND private=false) LIMIT 6 OFFSET {}".format(file_name.replace("'","''"), offset))
    await conn.close()
    return values;

async def find_file_by_id(file_id):
    conn = await asyncpg.connect(user='postgres', password='werdwerd',
                                 database='files_new', host='194.67.205.185')
    values = await conn.fetch("SELECT file_name, file_id, owner_id, create_date, private FROM all_files WHERE file_id = '{}'".format(file_id))
    await conn.close()
    if len(values)>0:
        return values[0];
    else:
        return None;

async def find_file_by_user_id(user_id, offset = 0):
    conn = await asyncpg.connect(user='postgres', password='werdwerd',
                                 database='files_new', host='194.67.205.185')
    values = await conn.fetch("SELECT file_name, file_id FROM all_files WHERE owner_id = {} LIMIT 6 OFFSET {}".format(user_id, offset))
    await conn.close()
    if len(values)>0:
        return values;
    else:
        return [];

async def delete_file_by_id(file_id, user_id):
    conn = await asyncpg.connect(user='postgres', password='werdwerd',
                                 database='files_new', host='194.67.205.185')
    values = await conn.execute("""DELETE FROM all_files WHERE (file_id = '{}' AND owner_id = {}) """.format(file_id, user_id))
    
    if values.split(" ")[-1]=='0':
        await conn.close()
        return 0; #nothing deleted
    else:
        await conn.execute("""UPDATE users SET files_count = files_count - 1 WHERE user_id = {}""".format(user_id))
        await conn.close()
        return 1; #deleted file

async def insert_file_all(file_name, file_id, owner_id, timestamp):
    conn = await asyncpg.connect(user='postgres', password='werdwerd',
                                 database='files_new', host='194.67.205.185')
    values = await conn.execute('''INSERT INTO all_files(file_name, file_id, owner_id, create_date) VALUES('{}', '{}', {}, '{}')'''.format(file_name, file_id, owner_id, timestamp))
    await conn.close()

async def insert_user(user_id, user_name, user_lang):
    conn = await asyncpg.connect(user='postgres', password='werdwerd',
                                 database='files_new', host='194.67.205.185')
    values = await conn.execute("""INSERT INTO users(user_id, user_name, user_lang, files_count) VALUES('{}', '{}', '{}', 0) ON CONFLICT (user_id) DO NOTHING RETURNING 0;""".format(str(user_id).replace("'","''"), user_name, user_lang))
    await conn.close()
    if values.split(" ")[-1]=='0':
        return 0; #nothing added
    else:
        return 1; 

async def find_user(user_id):
    conn = await asyncpg.connect(user='postgres', password='werdwerd',
                                 database='files_new', host='194.67.205.185')
    values = await conn.fetch("SELECT user_name, user_id, user_lang, files_count FROM users WHERE user_id = '{}'".format(user_id))
    await conn.close()
    if len(values)==1:
        return values[0];
    else:
        return None;


'''
async def f():
    for i in open("data.txt", "r"):
        i = i.split("	")
        print(i);
        await loop.create_task(insert_file_all(i[0], i[1], i[2], i[3]))
'''
#loop = asyncio.get_event_loop()
#loop.run_until_complete(f())

