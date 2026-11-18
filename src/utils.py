import logging

from bs4 import BeautifulSoup, Tag
from requests import RequestException, Response
from requests_cache import CachedSession

from exceptions import ParserFindTagException


def get_response(session: CachedSession, url: str) -> Response | None:
    """Загрузить страницу и обработать ошибки HTTP-запроса."""
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True,
        )
        return None


def find_tag(
    soup: BeautifulSoup | Tag,
    tag: str,
    attrs: dict[str, str] | None = None,
) -> Tag:
    """Найти HTML-тег или вызвать исключение при его отсутствии."""
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag
