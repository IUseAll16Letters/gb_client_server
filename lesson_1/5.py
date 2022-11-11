"""5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com
и преобразовать результаты из байтовового в строковый тип на кириллице."""
import asyncio
import chardet
import subprocess

from typing import Optional


async def ping_url(url: str, *, command='ping') -> None:
    global ENCODING
    print(f'Pinging: \033[34m{url}\033[0m')
    result = await asyncio.create_subprocess_shell(
        f'{command} {url}',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    rest: tuple = await result.communicate()

    if not ENCODING:
        ENCODING = chardet.detect(rest[0]).get('encoding')

    print(rest[0].decode(ENCODING))


async def main() -> None:
    urls = ('yandex.ru', 'youtube.com', 'google.com')
    tasks = []

    print('Starting event loop')
    for url in urls:
        task = asyncio.create_task(ping_url(url))
        tasks.append(task)

    await asyncio.gather(*tasks)
    print('Event loop finished')


if __name__ == '__main__':
    ENCODING: Optional[str] = None
    asyncio.run(main())
