import asyncio
import sqlalchemy

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from sqlalchemy.ext.asyncio.engine import AsyncConnection


print(f'{sqlalchemy.__version__ = }')

engine = create_async_engine("sqlite+aiosqlite:///./users.db")
print(engine)


class AsyncConn:

    def __init__(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///./users.db")

    async def get_connection(self):

        async def handle_connection(connection: AsyncConnection):
            while True:
                command = input('actions: insert, quit, create, delete, show: ')
                print(f'\033[032mSelected {command = }\033[0m')
                if command == 'insert':
                    await connection.execute(text(f"INSERT INTO {input('table to insert: ')} "
                                                  f"VALUES ('{input('v1: ')}', 'input('v2: ')')"))
                    await connection.commit()
                elif command == 'delete':
                    await connection.execute(text(f"DROP TABLE IF EXISTS {input('del table: ')}"))
                    await connection.commit()
                elif command == 'quit':
                    break
                elif command == 'create':
                    sql = f"CREATE TABLE IF NOT EXISTS {input('table name: ')}" \
                          f"({input('par1 n: ')} {input('par1 type: ')})"
                    await connection.execute(text(sql))
                    await connection.commit()
                elif command == 'show':
                    pass
                else:
                    print('Error cmnd')

                tables = await connection.execute(text('select name from sqlite_schema'))
                print(f'available tables: {tables.all()}')

        async with self.engine.connect() as conn:
            conn: AsyncConnection
            # result = await conn.execute(text("CREATE TABLE IF NOT EXISTS test_1"
            #                                  "(par1 text, par2 text)"))
            print(f'Conn: {conn}')
            await asyncio.gather(asyncio.create_task(handle_connection(conn)))


async def main():
    methods = ['begin', 'close', 'closed', 'commit', 'connection', 'dialect', 'dispatch', 'engine', 'execute',
               'info', 'invalidate', 'invalidated', 'rollback', 'scalar', 'scalars', 'start', 'stream']
    print(methods)
    return await asyncio.gather(asyncio.create_task(AsyncConn().get_connection()))


result = asyncio.run(main())

