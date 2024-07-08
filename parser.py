import re
import time

from typing import Optional, Dict

from general import _get_channel_content, channels, patterns, Item, _get_text_without_tags, FeedType
from parser_exceptions import FeedTypeError

"""Эти данные будут храниться в БД"""


class RSSParser:
    _feed_type: FeedType
    _current_item_index: int
    _channel_content: str
    _items_dict: Dict[int, Item]

    def __init__(self, channel_rss_link: str):
        self._items_dict = {}
        self._channel_content = _get_channel_content(channel_rss_link)
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

        self._set_items_dict()
        self._current_item_index = -1

    # INFO: private methods

    def _set_items_dict(self):
        item_matches = re.finditer(patterns['get_items'], self._channel_content, re.DOTALL)
        start_index = 0
        for item_match in item_matches:
            item_str = item_match.group(1)

            item_title_match = re.search(patterns['get_item_title'], item_str, re.DOTALL)
            item_link_match = re.search(patterns['get_item_link'], item_str, re.DOTALL)
            item_description_match = re.search(patterns['get_item_description'], item_str, re.DOTALL)

            item_title = item_title_match.group(1) if item_title_match else None
            item_link = item_link_match.group(1) if item_link_match else None
            item_description = item_description_match.group(1) if item_description_match else None

            item: Item = Item(item_title, item_link, item_description)
            self._items_dict[start_index] = item
            start_index += 1

    def _prettify_item(self) -> Optional[Item]:
        current_item = self._items_dict.get(self._current_item_index)
        if current_item:
            pretty_title_match = re.search(patterns['get_pretty_param'], current_item.title, re.DOTALL)
            pretty_description_match = re.search(patterns['get_pretty_param'], current_item.description, re.DOTALL)

            pretty_title = pretty_title_match.group(1) if pretty_title_match else current_item.title
            pretty_description = pretty_description_match.group(
                1) if pretty_description_match else current_item.description
            pretty_description = _get_text_without_tags(pretty_description)
            pretty_title = _get_text_without_tags(pretty_title)
            pretty_item: Item = Item(pretty_title, current_item.link, pretty_description)
            return pretty_item

    # INFO: public methods

    def get_channel_title_and_description(self) -> Optional[Dict[Optional[str], Optional[str]]]:
        channel_info_match = re.search(patterns['get_channel_info'], self._channel_content, re.DOTALL)
        if channel_info_match:
            pretty_title, pretty_description = None, None
            pretty_title_match = re.search(patterns['get_item_title'], channel_info_match.group(1), re.DOTALL)
            if pretty_title_match:
                pretty_title = _get_text_without_tags(pretty_title_match.group(1))
            pretty_description_match = re.search(patterns['get_item_description'], channel_info_match.group(1), re.DOTALL)
            if pretty_description_match:
                pretty_description = _get_text_without_tags(pretty_description_match.group(1))
            return {'title': pretty_title, 'description': pretty_description}

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


def test_rss(channel_rss_link: str):
    start_time = time.time()
    parser = RSSParser(channel_rss_link)
    print(parser.get_channel_title_and_description())
    print(parser.get_next().__dict__)
    print(parser.get_next().__dict__)
    print(parser.get_next().__dict__)

    print(parser.get_prev().__dict__)
    print(parser.get_prev().__dict__)
    print(parser.get_prev().__dict__)

    print(parser.get_first().__dict__)
    print(parser.get_last().__dict__)

    end_time = time.time()
    print(f'Total time: {end_time - start_time}')


test_rss(channels.get('RBC'))
