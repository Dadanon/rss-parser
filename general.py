import re
from enum import IntEnum
from typing import Optional, List

import requests


def _get_items(content: str) -> List[re.Match[str]]:
    return re.findall(patterns['get_items'], content, re.DOTALL)


patterns = {
    'ensure_rss': r'<rss[^>].*?>',
    'ensure_atom': r'<feed xmlns="http://www.w3.org/2005/Atom"',
    # RSS patterns
    'get_channel_info': r'<channel>(.*?)<item>',
    'get_items': r'<item>(.*?)</item>',
    'get_item_link': r'<link>(.*?)</link>',
    'get_item_description': r'<description>(.*?)</description>',
    # Atom patterns
    'get_channel_info_atom': r'<feed xmlns="http://www.w3.org/2005/Atom"\s*[^>].*?>(.*?)<entry>',
    'get_channel_description_atom': r'<subtitle>(.*?)</subtitle',
    'get_entries': r'<entry>(.*?)</entry>',
    'get_link_info_atom': r'<link[^/]/>',  # Полное содержание ссылки и для канала, и для статьи
    'get_link_href_atom': r'href="([^"].*?)"',
    'get_item_link_atom': r'<link href="([^"].*?)"',
    'ensure_self_link': r'rel="self"',
    'ensure_alternate_link': r'rel="alternate"',
    'get_content_with_type': r'<content type="([^"].*?)">(.*?)</content>',
    # Common patterns
    'get_item_title': r'<title\s*[^>]*?>(.*?)</title>',
    'get_pretty_param': r'<!\[CDATA\[(.*?)]',
    'get_p_tags': r'<p>(.*?)</p>',
    'get_opening_tags': r'<[^>].*?>',
    'get_closing_tags': r'</.*?>',
    'get_open_close_tags': r'<[^/].*?/>'
}


class Item:
    title: Optional[str]
    link: Optional[str]
    description: Optional[str]
    description_type: Optional[str]  # Тип контента, актуален для Atom

    def __init__(self, title: Optional[str], link: Optional[str], description: Optional[str], description_type: Optional[str] = None):
        self.title = title
        self.link = link
        self.description = description
        if not self.title and not self.description:
            raise ValueError('Either title or description should be set')
        self.description_type = description_type


class FeedType(IntEnum):
    RSS = 0
    ATOM = 1


FEED_TYPE_PATTERN_DICT = {
    FeedType.RSS: {
        'get_items': patterns['get_items'],
        'get_channel_info': patterns['get_channel_info'],
        'get_item_link': patterns['get_item_link'],
        'get_item_description': patterns['get_item_description']
    },
    FeedType.ATOM: {
        'get_items': patterns['get_entries'],
        'get_channel_info': patterns['get_channel_info_atom'],
        'get_item_link': patterns['get_item_link_atom'],
        'get_item_description': patterns['get_content_with_type']
    }
}


channels = {
    # RSS
    'RBC': 'https://rssexport.rbc.ru/rbcnews/news/20/full.rss',
    'Habr': 'https://habr.com/ru/rss/articles/',
    'NOT_RSS': 'https://qna.habr.com/q/1138620',
    'Events': 'https://www.opennet.ru/opennews/opennews_review.rss',
    'BSD': 'https://www.opennet.ru/opennews/opennews_bsd.rss',
    'Mozilla': 'https://www.opennet.ru/opennews/opennews_mozilla_full.rss',
    'EurasiaDaily': 'https://eadaily.com/ru/rss/index.xml',
    'MinisterstvoOborony': 'https://function.mil.ru:443/rss_feeds/reference_to_general.htm?contenttype=xml',
    'Nant': 'http://www.nantes.fr/rss/content/actualites.rss',
    'Tartu': 'https://www.tartu.ee/ru/rss',
    # Atom
    'Reddit': 'https://www.reddit.com/r/programming/.rss',
    'Nasa': 'https://www.nasa.gov/rss/dyn/breaking_news.rss',
    'NYTimes': 'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml?format=atom',
    'github': 'https://github.com/atom/atom/commits/master.atom'
}


def _get_channel_content(channel_rss_link: str) -> Optional[str]:
    if channel_rss_link:
        try:
            channel_content: str = requests.get(channel_rss_link, timeout=5, verify=False).text
            return channel_content
        except (requests.exceptions.ReadTimeout, requests.exceptions.ProxyError):
            return None


def _get_text_without_tags(text: str) -> str:
    pretty_text_match = re.search(patterns['get_pretty_param'], text, re.DOTALL)
    pretty_text = pretty_text_match.group(1) if pretty_text_match else text

    # Заменить lt gt на закрывающие / открывающие кавычки
    pretty_text = pretty_text.replace('&lt;', '<').replace('&gt;', '>')

    open_tag_matches = set(re.findall(patterns['get_opening_tags'], pretty_text, re.DOTALL))
    for open_tag_match in open_tag_matches:
        pretty_text = pretty_text.replace(open_tag_match, '')

    close_tag_matches = set(re.findall(patterns['get_closing_tags'], pretty_text, re.DOTALL))
    for close_tag_match in close_tag_matches:
        pretty_text = pretty_text.replace(close_tag_match, '')

    open_close_tag_matches = set(re.findall(patterns['get_open_close_tags'], pretty_text, re.DOTALL))
    for open_close_tag_match in open_close_tag_matches:
        pretty_text = pretty_text.replace(open_close_tag_match, '')

    pretty_text = (
        pretty_text
        .replace('\r\n', ' ')
        .replace('\n', ' ')
        .replace('&nbsp;', ' ')
        .replace(u'\xa0', u' ')
        .replace('&mdash;', '-')
        .replace('&laquo;', '"')
        .replace('&raquo;', '"')
        .replace('&apos;', '\'')
        .replace('&quot;', '"')
        .replace('&#8230;', '…')
        .replace('&amp;', '&')
        .replace('&#39;', '\'')
    )

    pretty_text = re.sub('\s+', ' ', pretty_text)

    return pretty_text
