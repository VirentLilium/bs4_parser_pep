from pathlib import Path

# Пути к директориям и файлам проекта.
BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR_NAME = 'downloads'
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'parser.log'
RESULTS_DIR_NAME = 'results'

# Адреса сайтов для парсинга.
MAIN_DOC_URL = 'https://docs.python.org/3/'
PEP_PYTHON_URL = 'https://peps.python.org/'

# Настройки обработки данных.
ENCODING = 'utf-8'
FILE_DIALECT = 'unix'
PARSER_FEATURES = 'lxml'

# Настройки логирования.
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
DT_FORMAT = '%d.%m.%Y %H:%M:%S'
LOG_FORMAT = '%(asctime)s - [%(levelname)s] - %(message)s'
LOG_MAX_BYTES = 10**6
LOG_BACKUP_COUNT = 5

# Настройки аргументов командной строки.
PARSER_DESCRIPTION = 'Парсер документации Python'
MODE_HELP = 'Режимы работы парсера'
CLEAR_CACHE_HELP = 'Очистка кеша'
OUTPUT_HELP = 'Дополнительные способы вывода данных'
PRETTY_OUTPUT = 'pretty'
FILE_OUTPUT = 'file'
OUTPUT_CHOICES = (PRETTY_OUTPUT, FILE_OUTPUT)

# Допустимые статусы PEP.
EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
