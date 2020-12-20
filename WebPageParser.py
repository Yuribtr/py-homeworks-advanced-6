import time
from datetime import date, timedelta
from typing import Union
import requests
from tqdm import tqdm
from lxml import html, etree
from lxml.html import HtmlElement


class WebPageParser:
    def __init__(self, url: str, request_delay=0.2):
        self.__url = url
        self.__request_delay = request_delay
        self.__tree = self.__load_page(url)
        # XPath's for preview
        self.__article_xpath = '//article'
        self.__title_xpath = '//article/h2/a'
        self.__link_xpath = '//article/h2/a/@href'
        self.__time_xpath = '//article/header/span'
        # XPath's for full page
        self.__article_inner_xpath = '//article'

    @staticmethod
    def __load_page(url):
        try:
            response = requests.get(url)
        except requests.exceptions.ConnectionError or requests.exceptions.InvalidSchema:
            return None
        if not (200 <= response.status_code < 300):
            return None
        return html.fromstring(response.text)

    @staticmethod
    def __tree_to_str(el):
        if isinstance(el, etree._ElementUnicodeResult):
            return el
        return etree.tostring(el, encoding='utf8', method='text').decode(encoding='utf8')

    @staticmethod
    def __normalize_date(article_date):
        article_date = article_date.replace('сегодня', date.today().strftime('%d.%m.%Y'))
        article_date = article_date.replace('вчера', (date.today() - timedelta(days=1)).strftime('%d.%m.%Y'))
        return article_date

    def __get_tags(self, xpath, position: Union[str, int] = 'all', tree: HtmlElement = None) -> Union[list, str]:
        """
        Extract tag by XPath and return only viewable text as one string, using position number if several tags found
        """
        tree = tree if tree is not None else self.__tree
        tags_raw = tree.xpath(xpath)
        tag = [self.__tree_to_str(tag) for tag in tags_raw]
        if position == 'all':
            return tag
        else:
            return tag[position]

    def search_words(self, words) -> list:
        result = []
        if self.__tree is None:
            print('Page not found: ' + self.__url)
            return result
        print('Searching main page for key words. Pls wait...')
        if not isinstance(words, list):
            words = [words]
        for pos, article in enumerate(tqdm(self.__get_tags(self.__article_xpath))):
            article_words = article.lower().split()
            article_link = self.__get_tags(self.__link_xpath, pos)
            found = False
            for word in words:
                if any([word in article_word for article_word in article_words]):
                    found = True
                    article_date = self.__normalize_date(self.__get_tags(self.__time_xpath, pos))
                    article_title = self.__get_tags(self.__title_xpath, pos)
                    result.append(f'<{article_date.strip()}> - <{article_title.strip()}> - <{article_link}>')
                    break
            # only if we're unable to find keywords in preview, making search inside full page
            if not found:
                if self.__scan_page(article_link, words):
                    article_date = self.__normalize_date(self.__get_tags(self.__time_xpath, pos))
                    article_title = self.__get_tags(self.__title_xpath, pos)
                    result.append(f'<{article_date.strip()}> - <{article_title.strip()}> - <{article_link}>')
        return result

    def __scan_page(self, url, words):
        # small delay to prevent ban
        time.sleep(self.__request_delay)
        tree = self.__load_page(url)
        article = self.__get_tags(self.__article_inner_xpath, 0, tree=tree)
        article_words = article.lower().split()
        for word in words:
            if any([word in article_word for article_word in article_words]):
                return True
        return False
