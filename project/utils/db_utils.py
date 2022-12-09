__all__ = ['setup_db', 'process_group_request', 'get_users_group_if_permit', 'save_user_message',
           'save_connection_data']

from typing import Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from project.utils.config import *


async def setup_db(conn: AsyncConnection) -> None:
    await conn.execute(text(f'DROP TABLE IF EXISTS connections'))
    await conn.execute(text(f'CREATE TABLE IF NOT EXISTS connections ('
                            f'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                            f'peername TEXT,'
                            f'event_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,'
                            f'is_leaving BOOl)'))

    await conn.execute(text(f'DROP TABLE IF EXISTS users'))
    await conn.execute(text(f'CREATE TABLE IF NOT EXISTS users ('
                            f'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                            f'name VARCHAR(50),'
                            f'password VARCHAR(100),'
                            f'created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'))

    if DEBUG:
        s = text(f"INSERT INTO users (name, password) VALUES (:un, :up)")
        for i in range(1, 4):
            await conn.execute(s, {'un': f'u{i}', 'up': TEST_PASSWORD})

    await conn.execute(text(f'DROP TABLE IF EXISTS user_messages'))
    await conn.execute(text(f'CREATE TABLE IF NOT EXISTS user_messages ('
                            f'id INTEGER PRIMARY KEY AUTOINCREMENT,'
                            f'from_user VARCHAR(50),'
                            f'to_user VARCHAR(50),'
                            f'body TEXT,'
                            f'created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,'
                            f'FOREIGN KEY(from_user) REFERENCES users(id),'
                            f'FOREIGN KEY(to_user) REFERENCES users(id))'))

    await conn.execute(text(f'DROP TABLE IF EXISTS groups'))
    await conn.execute(text(f'CREATE TABLE IF NOT EXISTS groups ('
                            f'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                            f'name VARCHAR(55), '
                            f'user_id INTEGER NOT NULL, '
                            f"description TEXT DEFAULT 'no description', "
                            f'created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, '
                            f'FOREIGN KEY(user_id) REFERENCES users(id))'))

    await conn.execute(text(f'DROP TABLE IF EXISTS user_group'))
    await conn.execute(text(f'CREATE TABLE IF NOT EXISTS user_group ('
                            f'id INTEGER PRIMARY KEY AUTOINCREMENT, '
                            f'user_id INTEGER NOT NULL, '
                            f'group_id INTEGER NOT NULL, '
                            f"status VARCHAR(35) DEFAULT 'simple user', "
                            f'created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, '
                            f'FOREIGN KEY(user_id) REFERENCES users(id), '
                            f'FOREIGN KEY(group_id) REFERENCES groups(id))'))

    await conn.commit()


async def process_group_request(request: Message, conn: AsyncConnection, username: str,
                                group_name: str = None, **kwargs) -> Tuple[bool, str]:
    status = 'user'
    params = {'gn': group_name, 'un': username, 'st': status}

    if request is Message.create:
        if await group_exists(group_name, conn):
            return False, f'Group {group_name} already exist'

        if 'description' in kwargs:
            sql = f"INSERT INTO groups (name, user_id, description) " \
                  f"SELECT :gn, u.id, :dsc " \
                  f"FROM groups g INNER JOIN users u ON u.name == :un"
            params.update({'dsc': kwargs['descriptions']})
        else:
            sql = f"INSERT INTO groups (name, user_id) " \
                  f"SELECT :gn, u.id " \
                  f"FROM users u " \
                  f"WHERE u.name == :un"

        await conn.execute(text(sql), params)
        status = 'owner'

    elif request is Message.leave:
        if await group_exist_user_in_group(params, conn):
            # TODO, Hello sqlite!
            await conn.execute(
                text(f"DELETE FROM user_group "
                     f"WHERE user_id == (SELECT id FROM users WHERE name == :un) "
                     f"AND group_id == (SELECT id FROM groups WHERE name == :gn)"),
                params
            )
            await conn.commit()
            return True, f'You have left {group_name}'

        else:
            return False, f'You are not in {group_name}'

    elif request is Message.join:
        if await group_exist_user_in_group(params, conn):
            return False, f"Group {group_name} doesn't exist or you are not in it"

    elif request is Message.party:
        resp = await user_groups(username, conn)
        return True, resp

    await conn.execute(text(f'INSERT INTO user_group (user_id, group_id, status) '
                            f"SELECT u.id, g.id, :st "
                            f"FROM groups g LEFT JOIN users u "
                            f"WHERE u.name == :un AND g.name == :gn"), params)

    await conn.commit()

    return True, f'you have joined {group_name} as {status}'


async def get_users_group_if_permit(group_name: str, from_user: str, conn: AsyncConnection) -> Tuple[bool, str]:
    params = {'gn': group_name, 'un': from_user}

    if await group_exist_user_in_group(params, conn):
        usernames = await conn.execute(
            text(f"SELECT u.name "
                 f"FROM user_group ug "
                 f"LEFT JOIN groups g on g.id == ug.group_id "
                 f"LEFT JOIN users u on u.id == ug.user_id "
                 f"WHERE g.name == :gn"),
            params)
        return True, usernames.all()

    return False, "Group doesn't exist or you are not in it"


async def group_exist_user_in_group(group_user_name_params: dict, conn: AsyncConnection) -> bool:
    result = await conn.execute(
        text(f"SELECT u.name "
             f"FROM user_group ug "
             f"LEFT JOIN groups g on g.id == ug.group_id "
             f"LEFT JOIN users u on u.id == ug.user_id "
             f"WHERE g.name == :gn AND u.name == :un"),
        group_user_name_params
    )

    return bool(result.all())


async def group_exists(group_name: str, conn: AsyncConnection) -> bool:
    result = await conn.execute(
        text(f"SELECT * FROM groups g "
             f"WHERE g.name == :gn"),
        {'gn': group_name}
    )
    return bool(result.all())


async def user_groups(username: str, conn: AsyncConnection) -> str:
    result = await conn.execute(
        text(f"SELECT g.name "
             f"FROM user_group ug "
             f"LEFT JOIN groups g on g.id == ug.group_id "
             f"LEFT JOIN users u on u.id == ug.user_id "
             f"WHERE u.name == :un"),
        {'un': username}
    )
    result = result.all()
    return f"You are member of {', '.join(i[0] for i in result)} groups" if result else "You aren't joined in any grp"


async def save_user_message(from_user: str, to_user: str, body: str, conn: AsyncConnection) -> None:
    await conn.execute(
        text(f"INSERT INTO user_messages (from_user, to_user, body)"
             f"SELECT u.id, :to, :bdy "
             f"FROM users u "
             f"WHERE u.name == :frm"),
        {'frm': from_user, 'to': to_user, 'bdy': body}
    )
    await conn.commit()


async def create_new_user(user_data: tuple, conn: AsyncConnection) -> Tuple[bool, str]:
    username, pwd = user_data[0], user_data[1]
    user_created = await conn.execute(
        text("SELECT * FROM users WHERE name == :un"),
        {'un': username}
    )
    if user_created.all():
        return False, f'User {username} already exist'


async def save_connection_data(addr_pair: tuple, conn: AsyncConnection, connected: bool = False) -> None:
    user_addr = str(addr_pair).replace("'", '')

    await conn.execute(
        text(f"INSERT INTO connections (peername, is_leaving)"
             f"VALUES (:peer, :lv)"),
        {'peer': user_addr, 'lv': connected}
    )
    await conn.commit()
