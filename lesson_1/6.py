"""6. Создать текстовый файл test_file.txt, заполнить его тремя строками:
«сетевое программирование», «сокет», «декоратор». Проверить кодировку файла по умолчанию.
Принудительно открыть файл в формате Unicode и вывести его содержимое."""
import locale


def create_cp1251_file(filename: str) -> None:
    print(f'Saving data to file: \033[32m{filename}\033[0m')
    DATA_TO_WRITE = ('сетевое программирование', 'сокет', 'декоратор')

    with open(filename, 'w') as f:
        print(f'File to write default encoding is: \033[32m{f.encoding}\033[0m')
        for data in DATA_TO_WRITE:
            f.writelines(data + '\n')


def read_from_file(filename: str, default_encoding: str = 'utf-8') -> None:
    print(f'Reading data from file: \033[32m{filename}\033[0m')

    with open(filename, 'r', encoding=default_encoding, errors='replace') as f:
        line = f.readline()

        if line:
            print('File output is: \033[34m')

            while line:
                print(line.replace('\n', ''))
                line = f.readline()
            print('\033[0m')
        else:
            print('File is empty')


def main() -> None:
    FILENAME = 'test_file.txt'
    create_cp1251_file(FILENAME)
    read_from_file(FILENAME)


if __name__ == '__main__':
    print(f'Locale default encoding: \033[32m{locale.getpreferredencoding()}\033[0m')
    main()
