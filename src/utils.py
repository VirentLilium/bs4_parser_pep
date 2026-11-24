from __future__ import annotations

from bs4 import BeautifulSoup, Tag
from requests import RequestException, Response
from requests_cache import CachedSession

from src.constants import ENCODING, EXPECTED_STATUS, PARSER_FEATURES
from src.exceptions import PageLoadException, ParserFindTagException


def get_response(
    session: CachedSession,
    url: str,
    encoding: str = ENCODING,
) -> Response:
    """Загрузить страницу с указанной кодировкой."""
    try:
        response = session.get(url)
        response.raise_for_status()
    except RequestException as error:
        raise PageLoadException(
            f'Возникла ошибка при загрузке страницы {url}: {error}'
        ) from error

    response.encoding = encoding
    return response


def get_soup(
    session: CachedSession, url: str, features: str = PARSER_FEATURES
) -> BeautifulSoup:
    """Загрузить HTML-страницу и создать объект BeautifulSoup."""
    response = get_response(session, url)
    return BeautifulSoup(response.text, features)


def find_tag(
    soup: BeautifulSoup | Tag,
    tag: str,
    attrs: dict[str, str] | None = None,
) -> Tag:
    """Найти HTML-тег или вызвать исключение при его отсутствии."""
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(f'Не найден тег {tag} {attrs}')
    return searched_tag


def get_pep_status(soup: BeautifulSoup, pep_url: str) -> str:
    """Получить фактический статус документа PEP."""
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


def parse_pep(
    session: CachedSession,
    link_url: str,
    preview_status: str,
) -> tuple[str, str | None]:
    """Получить статус PEP и проверить его соответствие общему списку."""
    soup = get_soup(session, link_url)
    actual_status = get_pep_status(soup, link_url)

    expected_statuses = EXPECTED_STATUS[preview_status]
    mismatch = None

    if actual_status not in expected_statuses:
        mismatch = (
            f'{link_url}\n'
            f'Статус в карточке: {actual_status}\n'
            f'Ожидаемые статусы: {list(expected_statuses)}'
        )
    return actual_status, mismatch
