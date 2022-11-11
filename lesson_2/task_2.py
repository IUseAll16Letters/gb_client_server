"""
2. Задание на закрепление знаний по модулю json. Есть файл orders
в формате JSON с информацией о заказах. Написать скрипт, автоматизирующий
его заполнение данными.

Для этого:
Создать функцию write_order_to_json(), в которую передается
5 параметров — товар (item), количество (quantity), цена (price),
покупатель (buyer), дата (date). Функция должна предусматривать запись
данных в виде словаря в файл orders.json. При записи данных указать
величину отступа в 4 пробельных символа;
Проверить работу программы через вызов функции write_order_to_json()
с передачей в нее значений каждого параметра.

ПРОШУ ВАС НЕ УДАЛЯТЬ ИСХОДНЫЙ JSON-ФАЙЛ
ПРИМЕР ТОГО, ЧТО ДОЛЖНО ПОЛУЧИТЬСЯ

{
    "orders": [
        {
            "item": "принтер",
            "quantity": "10",
            "price": "6700",
            "buyer": "Ivanov I.I.",
            "date": "24.09.2017"
        },
        {
            "item": "scaner",
            "quantity": "20",
            "price": "10000",
            "buyer": "Petrov P.P.",
            "date": "11.01.2018"
        },
        {
            "item": "scaner",
            "quantity": "20",
            "price": "10000",
            "buyer": "Petrov P.P.",
            "date": "11.01.2018"
        },
        {
            "item": "scaner",
            "quantity": "20",
            "price": "10000",
            "buyer": "Petrov P.P.",
            "date": "11.01.2018"
        }
    ]
}

вам нужно подгрузить JSON-объект
и достучаться до списка, который и нужно пополнять
а потом сохранять все в файл
"""
import csv
import json
import datetime

from pathlib import Path


def get_now_with_timezone(hour_offset: int = 3, timezone_name: str = 'Moscow') -> datetime.datetime:
    offset = datetime.timedelta(hours=hour_offset)
    timezone = datetime.timezone(offset, name=timezone_name)
    return datetime.datetime.now(tz=timezone)


class UnknownFormatError(NotImplementedError):
    pass


class FileProcessor:
    _formats = {}

    def __init_subclass__(cls, prefix, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._formats[prefix] = cls

    def __new__(cls, path: str):
        filename, sep, resolution = path.rpartition('.')
        subclass = cls._formats.get(resolution)

        if not subclass:
            raise UnknownFormatError

        obj = object.__new__(subclass)
        obj.fname = ''.join((filename, sep, resolution))

        return obj

    def read_self_data(self) -> None:
        raise NotImplementedError

    def write_data(self, *args, **kwargs) -> None:
        raise NotImplementedError


class CsvProcessor(FileProcessor, prefix='csv'):

    def read_self_data(self) -> dict:
        with open(self.fname, 'r') as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader)
            for data_row in csv_reader:
                yield {title: data for title, data in zip(headers, data_row)}


class JsonProcessor(FileProcessor, prefix='json'):

    def read_self_data(self) -> dict:
        print(f'Reading {self.fname}')
        with open(self.fname, 'r', encoding='utf-8') as f:
            object_to_write = json.load(f)

        return object_to_write

    def write_data(self, item: str, quantity: str, price: str, buyer: str, date: str, kw_object: str,
                   result_filedir: str = './result_files') -> None:
        result_data = self.read_self_data()

        if not result_data.get(kw_object):
            new_file_name = Path(result_filedir) / get_now_with_timezone() \
                .strftime(f'task_2_orders_%y_%m_%d_%H_%M_filled.json')
            self.fname = new_file_name

        save_object = {'item': item, 'quantity': quantity, 'price': price, 'buyer': buyer, 'date': date}
        result_data.get(kw_object).append(save_object)

        with open(self.fname, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=4, ensure_ascii=False)


def main():
    js = JsonProcessor('./task_2_files/orders.json')

    for order in CsvProcessor('./task_2_files/data.csv').read_self_data():
        js.write_data(**order, kw_object='orders')


if __name__ == '__main__':
    main()
