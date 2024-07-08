import re
import time

from typing import Optional, Dict, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from general import _get_link_content, channels, patterns, Item, _get_text_without_tags, FeedType, \
    FEED_TYPE_PATTERN_DICT
from parser_exceptions import FeedTypeError

"""Эти данные будут храниться в БД"""


class RSSParser:
    _feed_type: FeedType
    _current_item_index: int
    _channel_content: str
    _channel_title: str
    _channel_description: str
    _items_dict: Dict[int, Item]
    _patterns_dict: dict  # Словарь шаблонов в зависимости от self._feed_type
    _chrome_options: Options  # Параметр для эмуляции пользователя при получении контента страницы

    def __init__(self, channel_rss_link: str):
        self._items_dict = {}
        self._channel_content = _get_link_content(channel_rss_link)
        if not self._channel_content:
            raise ValueError(f"Не удалось спарсить RSS контент по указанной ссылке: {channel_rss_link}")
        is_rss = re.search(patterns['ensure_rss'], self._channel_content, re.DOTALL)
        if is_rss:
            self._feed_type = FeedType.RSS
        else:
            is_atom = re.search(patterns['ensure_atom'], self._channel_content, re.DOTALL)
            if is_atom:
                self._feed_type = FeedType.ATOM
            else:
                raise FeedTypeError("Неизвестный формат файла: не RSS и не Atom")
        self._patterns_dict = FEED_TYPE_PATTERN_DICT.get(self._feed_type)
        title_and_description = self._get_channel_title_and_description()
        if title_and_description:
            self._channel_title, self._channel_description = title_and_description
        self._set_items_dict()
        self._current_item_index = -1
        self._chrome_options = Options()
        self._chrome_options.add_argument('--headless')
        self._chrome_options.add_argument('--disable-gpu')

    # INFO: private methods

    def _get_channel_title_and_description(self) -> Optional[Tuple[str, str]]:
        channel_info_match = re.search(self._patterns_dict.get('get_channel_info'), self._channel_content, re.DOTALL)
        if channel_info_match:
            pretty_title, pretty_description = None, None
            pretty_title_match = re.search(patterns['get_item_title'], channel_info_match.group(1), re.DOTALL)
            if pretty_title_match:
                pretty_title = _get_text_without_tags(pretty_title_match.group(1))
            pretty_description_match = re.search(self._patterns_dict.get('get_item_description'),
                                                 channel_info_match.group(1),
                                                 re.DOTALL)
            if pretty_description_match:
                pretty_description = _get_text_without_tags(pretty_description_match.group(1))
            return pretty_title, pretty_description

    def _set_items_dict(self):
        item_matches = re.finditer(self._patterns_dict.get('get_items'), self._channel_content, re.DOTALL)
        start_index = 0
        for item_match in item_matches:
            item_str = item_match.group(1)

            item_title_match = re.search(patterns['get_item_title'], item_str, re.DOTALL)
            item_link_match = re.search(self._patterns_dict.get('get_item_link'), item_str, re.DOTALL)
            item_description_match = re.search(self._patterns_dict.get('get_item_description'), item_str, re.DOTALL)

            item_title = item_title_match.group(1) if item_title_match else None
            item_link = item_link_match.group(1) if item_link_match else None
            try:
                item_description_type, item_description = _get_text_without_tags(item_description_match.group(1)), _get_text_without_tags(item_description_match.group(2))
            except IndexError:
                item_description, item_description_type = item_description_match.group(1), None

            item: Item = Item(item_title, item_link, item_description, item_description_type)
            self._items_dict[start_index] = item
            start_index += 1

    def _prettify_item(self) -> Optional[Item]:
        current_item = self._items_dict.get(self._current_item_index)
        if current_item:
            if not current_item.description_type or current_item.description_type == 'html':
                pretty_description = _get_text_without_tags(current_item.description)
            else:
                pretty_description = current_item.description
            pretty_title = _get_text_without_tags(current_item.title)
            pretty_item: Item = Item(pretty_title, current_item.link, pretty_description)
            return pretty_item

    # INFO: public methods

    def get_channel_title_and_description(self) -> Optional[Dict[Optional[str], Optional[str]]]:
        return {'title': self._channel_title, 'description': self._channel_description}

    def get_next(self) -> Optional[Item]:
        next_index = self._current_item_index + 1
        self._current_item_index = next_index if 0 <= next_index < self.items_length else 0
        return self._prettify_item()

    def get_prev(self) -> Optional[Item]:
        prev_index = self._current_item_index - 1
        self._current_item_index = prev_index if 0 <= prev_index < self.items_length else self.items_length - 1
        return self._prettify_item()

    def get_first(self) -> Optional[Item]:
        self._current_item_index = 0
        return self._prettify_item()

    def get_last(self) -> Optional[Item]:
        self._current_item_index = self.items_length - 1
        return self._prettify_item()

    @property
    def items_length(self) -> int:
        return len(self._items_dict)

    def get_item_content(self) -> Optional[str]:
        current_item_link = self._items_dict.get(self._current_item_index).link
        if current_item_link:
            driver = webdriver.Chrome(options=self._chrome_options)
            print(f'\n\n\nCurrent item: {self._items_dict.get(self._current_item_index).__dict__}\n\n\n')
            print(f'\n\n\nCurrent url: {current_item_link}\n\n\n')
            driver.get(current_item_link)
            body_text = driver.find_element(By.TAG_NAME, 'body').text  # Пока самое простое - получаем текст тега body
            return body_text


def test_rss(channel_rss_link: str):
    try:
        start_time = time.time()
        parser = RSSParser(channel_rss_link)

        print(parser.get_channel_title_and_description())
        print(parser.get_next().__dict__)
        print(parser.get_prev().__dict__)
        print(parser.get_first().__dict__)
        print(parser.get_last().__dict__)

        end_time = time.time()
        print(f'Total time: {end_time - start_time}')
    except (ValueError, FeedTypeError) as e:
        print(f'Error: {e}')
        return


# for _, channel_link in channels.items():
#     test_rss(channel_link)


def test_item_detail(channel_rss_link: str):
    try:
        start_time = time.time()
        parser = RSSParser(channel_rss_link)

        next_item: Optional[Item] = parser.get_next()
        if next_item:
            print(parser.get_item_content())

        end_time = time.time()
        print(f'\n\nTotal time: {end_time - start_time}')
    except (ValueError, FeedTypeError) as e:
        print(f'Error: {e}')
        return


# for _, channel_link in channels.items():
#     test_item_detail(channel_link)


test_item_detail(channels.get('RBC'))
