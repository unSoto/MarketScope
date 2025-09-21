"""
Configuration settings for MarketScope - HH.ru Vacancy Scraper
Version: 1.0.0
Author: Скрауч Владислав Игоревич
"""

import os
from pathlib import Path

# Database configuration
DATABASE_PATH = "vacancies.db"

# Parser configuration
DEFAULT_PAGE_LIMIT = 5
REQUEST_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 1  # seconds

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
]

# Search parameters mapping
EXPERIENCE_MAPPING = {
    'noExperience': 'Нет опыта',
    'between1And3': 'От 1 до 3 лет',
    'between3And6': 'От 3 до 6 лет',
    'moreThan6': 'Более 6 лет'
}

# Location area IDs for hh.ru
LOCATION_MAPPING = {
    'Москва': '1',
    'Московская область': '2019',
    'Санкт-Петербург': '2',
    'Екатеринбург': '3',
    'Новосибирск': '4',
    'Краснодар': '53',
    'Нижний Новгород': '66',
    'Казань': '88',
    'Челябинск': '104',
    'Омск': '68',
    'Самара': '78',
    'Ростов-на-Дону': '76',
    'Уфа': '99',
    'Красноярск': '54',
    'Воронеж': '26',
    'Волгоград': '24',
    'Пермь': '72'
}

# GUI Configuration
WINDOW_TITLE = "HH.ru Vacancy Scraper"
WINDOW_SIZE = "1200x800"
MIN_WINDOW_SIZE = "1000x700"

# Export settings
DEFAULT_EXPORT_PATH = str(Path.home() / "Documents" / "vacancies_export")
SUPPORTED_EXPORT_FORMATS = ['csv', 'xlsx', 'json']

# Logging configuration
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = 'vacancy_scraper.log'

# Application settings
AUTO_SAVE_INTERVAL = 300  # seconds
MAX_SEARCH_HISTORY = 50
MAX_VACANCIES_DISPLAY = 1000

class Config:
    """Configuration manager class."""

    def __init__(self):
        self.database_path = DATABASE_PATH
        self.default_page_limit = DEFAULT_PAGE_LIMIT
        self.request_timeout = REQUEST_TIMEOUT
        self.delay_between_requests = DELAY_BETWEEN_REQUESTS
        self.user_agents = USER_AGENTS
        self.experience_mapping = EXPERIENCE_MAPPING
        self.location_mapping = LOCATION_MAPPING
        self.window_title = WINDOW_TITLE
        self.window_size = WINDOW_SIZE
        self.min_window_size = MIN_WINDOW_SIZE
        self.default_export_path = DEFAULT_EXPORT_PATH
        self.supported_export_formats = SUPPORTED_EXPORT_FORMATS
        self.log_level = LOG_LEVEL
        self.log_format = LOG_FORMAT
        self.log_file = LOG_FILE
        self.auto_save_interval = AUTO_SAVE_INTERVAL
        self.max_search_history = MAX_SEARCH_HISTORY
        self.max_vacancies_display = MAX_VACANCIES_DISPLAY

    def get_location_id(self, location_name: str) -> str:
        """Get area ID for location name."""
        return self.location_mapping.get(location_name, '113')  # Default to Russia

    def get_experience_display_name(self, experience_code: str) -> str:
        """Get display name for experience code."""
        return self.experience_mapping.get(experience_code, experience_code)

    def create_export_directory(self):
        """Create default export directory if it doesn't exist."""
        export_path = Path(self.default_export_path)
        export_path.mkdir(parents=True, exist_ok=True)
        return export_path

# Global configuration instance
config = Config()
