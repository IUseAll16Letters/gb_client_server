"""4. Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления
в байтовое и выполнить обратное преобразование (используя методы encode и decode)."""


def main() -> None:
    WORDS: tuple = ('разработка', 'админинстрирование', 'protocol', 'standard')
    for word in WORDS:
        print(word := word.encode('utf-8'), end=' | ')
        print(word := word.decode('utf-8'))


if __name__ == '__main__':
    main()
