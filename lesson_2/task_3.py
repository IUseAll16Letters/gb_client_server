"""
3. Задание на закрепление знаний по модулю yaml.
 Написать скрипт, автоматизирующий сохранение данных
 в файле YAML-формата.
Для этого:

Подготовить данные для записи в виде словаря, в котором
первому ключу соответствует список, второму — целое число,
третьему — вложенный словарь, где значение каждого ключа —
это целое число с юникод-символом, отсутствующим в кодировке
ASCII(например, €);

Реализовать сохранение данных в файл формата YAML — например,
в файл file.yaml. При этом обеспечить стилизацию файла с помощью
параметра default_flow_style, а также установить возможность работы
с юникодом: allow_unicode = True;

Реализовать считывание данных из созданного файла и проверить,
совпадают ли они с исходными.
"""
import yaml
from pathlib import Path


class DumpDataObject:
    def __init__(self, items: list, items_price: dict, items_quantity: int):
        self.items = items
        self.items_price = items_price
        self.items_quantity = items_quantity


def compare_yaml_files(file_1: Path, file_2: Path) -> None:
    with open(file_1, 'r', encoding='utf-8') as f1:
        with open(file_2, 'r', encoding='utf-8') as f2:
            file_1 = yaml.load(f1, Loader=yaml.Loader)
            file_2 = yaml.load(f2, Loader=yaml.Loader)
            assert dict(file_1.__dict__) == file_2, 'Files content are not equal'


def main() -> None:
    RESULT_FILE_NAME = Path('./result_files') / 'task_3_result.yaml'
    TEST_DIR = Path('./task_3_files/')
    EUR_SIGN = '\u20AC'

    data_to_dump = DumpDataObject(items=['computer', 'printer', 'keyboard', 'mouse'],
                                  items_price={'computer': f'200{EUR_SIGN}-1000{EUR_SIGN}',
                                               'keyboard': f'5{EUR_SIGN}-50{EUR_SIGN}',
                                               'mouse': f'4{EUR_SIGN}-7{EUR_SIGN}',
                                               'printer': f'100{EUR_SIGN}-300{EUR_SIGN}'},
                                  items_quantity=4)

    with open(RESULT_FILE_NAME, 'w', encoding='utf-8') as f:
        yaml.dump(data=data_to_dump, stream=f, indent=2, allow_unicode=True)

    compare_yaml_files(RESULT_FILE_NAME, TEST_DIR / 'file.yaml')


if __name__ == '__main__':
    main()
