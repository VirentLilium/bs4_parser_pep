from __future__ import annotations

import logging

from bs4 import BeautifulSoup, Tag
from requests import RequestException, Response
from requests_cache import CachedSession

from src.exceptions import ParserFindTagException


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


def get_pep_status(soup: BeautifulSoup, pep_url: str) -> str:
    """Получить фактический статус из карточки документа PEP."""
    dt_tags = soup.find_all('dt')
    for dt_tag in dt_tags:
        field_name = dt_tag.text.strip().rstrip(':')

        if field_name == 'Status':
            status_tag = dt_tag.find_next_sibling('dd')
            if status_tag is None:
                raise ParserFindTagException(
                    f'Не найден статус PEP: {pep_url}'
                )
            return status_tag.text.strip()
    raise ParserFindTagException(f'Не найдено поле Status: {pep_url}')
