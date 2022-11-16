"""
1. Задание на закрепление знаний по модулю CSV. Написать скрипт,
осуществляющий выборку определенных данных из файлов info_1.txt, info_2.txt,
info_3.txt и формирующий новый «отчетный» файл в формате CSV.

Для этого:

Создать функцию get_data(), в которой в цикле осуществляется перебор файлов
с данными, их открытие и считывание данных. В этой функции из считанных данных
необходимо с помощью регулярных выражений извлечь значения параметров
«Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
Значения каждого параметра поместить в соответствующий список. Должно
получиться четыре списка — например, os_prod_list, os_name_list,
os_code_list, os_type_list. В этой же функции создать главный список
для хранения данных отчета — например, main_data — и поместить в него
названия столбцов отчета в виде списка: «Изготовитель системы»,
«Название ОС», «Код продукта», «Тип системы». Значения для этих
столбцов также оформить в виде списка и поместить в файл main_data
(также для каждого файла);

Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл.
В этой функции реализовать получение данных через вызов функции get_data(),
а также сохранение подготовленных данных в соответствующий CSV-файл;

Изготовитель системы,Название ОС,Код продукта,Тип системы
1,LENOVO,Windows 7,00971-OEM-1982661-00231,x64-based
2,ACER,Windows 10,00971-OEM-1982661-00231,x64-based
3,DELL,Windows 8.1,00971-OEM-1982661-00231,x86-based
"""
import csv
import re

from chardet import detect
from pathlib import Path
from typing import Optional, List
from time import perf_counter


class NoTxtFilesFound(FileNotFoundError):
    pass


def get_dir_txt_files(dirname: Path) -> list:
    txt_files = [file for file in dirname.iterdir() if file.name.endswith('.txt')]
    if not txt_files:
        raise NoTxtFilesFound(f'There are no txt files in {dirname} folder')
    return txt_files


def get_file_encoding(file_sample: str, sample_string: Optional[bytes] = None) -> str:
    if sample_string:
        return detect(sample_string).get('encoding')
    with open(file_sample, 'rb') as f:
        return detect(f.readline()).get('encoding')


def parse_required_data(line: str, required_fields: List) -> Optional[tuple]:
    for field in required_fields:
        if re.search(field, line) is not None:
            required_data = line.split(':')[-1].strip()
            if field == 'Название ОС':
                required_data = re.search(
                    r'(windows [\d/.]*)|(linux .*)', required_data, re.I)\
                    .group().strip()

            return (field, required_data.replace(' PC', ''))

    return None


def get_data_from_txt(file_name: str, required_fields: list) -> list:
    print(f'Reading: {file_name}')
    with open(file_name, 'r', encoding=get_file_encoding(file_name)) as f:

        output = REQUIRED_FIELDS.copy()

        for line in f.readlines():
            parsed_line_data = parse_required_data(line, required_fields)
            if parsed_line_data:
                required_fields.remove(list(parsed_line_data)[0])
                output[REQUIRED_FIELDS.index(parsed_line_data[0])] = parsed_line_data[1]

            if not required_fields:
                break

    return output


def write_to_csv(files: List[str]) -> None:
    with open('./result_files/task_1_result.csv', 'w', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(['№'] + REQUIRED_FIELDS)
        for idx, file in enumerate(files, 1):
            csv_writer.writerow([idx] + get_data_from_txt(file, REQUIRED_FIELDS.copy()))


def main() -> None:
    global REQUIRED_FIELDS
    REQUIRED_FIELDS = ['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']
    WORKDIR = './task_1_files'

    try:
        filenames = get_dir_txt_files(Path(WORKDIR))
        write_to_csv(filenames)
    except NoTxtFilesFound as e:
        print(e)


if __name__ == '__main__':
    for _ in range(10):
        start = perf_counter()
        main()
        print(perf_counter() - start)
