"""3. Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в байтовом типе."""


def main() -> None:
    WORDS: tuple = ('attribute', 'type', 'класс', 'функция')
    print(WORDS)

    for word in WORDS:
        try:
            print(eval(f'b"{word}"'))
        except SyntaxError:
            print(f"Can't convert to bytes: {word}")


if __name__ == '__main__':
    main()
