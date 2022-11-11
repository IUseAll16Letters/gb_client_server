"""2. Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования в последовательность
кодов (не используя методы encode и decode) и определить тип, содержимое и длину соответствующих переменных."""


def main() -> None:
    WORDS: tuple = (b'class', b'function', b'method')
    for word in WORDS:
        print(word, f' | type: {type(word)} | length: {len(word)}')


if __name__ == '__main__':
    main()
