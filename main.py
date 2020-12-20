from WebPageParser import WebPageParser

KEYWORDS = ['дизайн', 'фото', 'web', 'python']


if __name__ == '__main__':
    parser = WebPageParser('https://habr.com/ru/all/')
    print(*parser.search_words(KEYWORDS), sep='\n')
