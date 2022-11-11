import csv
import re

from chardet import detect
from typing import Optional, List
from time import perf_counter


def get_file_encoding(file_sample: str, sample_string: Optional[bytes] = None) -> str:
    if sample_string:
        return detect(sample_string).get('encoding')
    with open(file_sample, 'rb') as f:
        return detect(f.readline()).get('encoding')


def get_data_from_txt(file_name: str):
    print(f'Reading: {file_name}')
    with open(file_name, 'r', encoding=get_file_encoding(file_name)) as f:
        file_data = f.read()
        result: dict = {}
        for field in REQUIRED_FIELDS:
            data = re.search(f'\n{field}: .*\n', file_data)
            if data is not None:
                data = data.group().split(':')[-1].strip()
                if field == 'Название ОС':
                    data = re.search(r'(windows [\d/.]*)', data, re.I).group().strip()
                result[field] = data.replace(' PC', '')

    return result


def write_to_csv(files: List[str]):
    with open('./result_files/task_1_a_result.csv', 'w', newline='') as f:
        csv_writer = csv.DictWriter(f, fieldnames=REQUIRED_FIELDS)
        csv_writer.writeheader()
        for file in files:
            csv_writer.writerow(get_data_from_txt(file))


def main():
    filenames = ['./task_1_files/info_1.txt', './task_1_files/info_2.txt', './task_1_files/info_3.txt']
    write_to_csv(filenames)


if __name__ == '__main__':
    REQUIRED_FIELDS = ['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']
    for _ in range(10):
        start = perf_counter()
        main()
        print(perf_counter() - start)
