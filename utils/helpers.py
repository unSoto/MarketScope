"""
Utility functions for HH.ru Vacancy Scraper
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Clean and normalize text data."""
    if not text:
        return ""

    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())

    # Remove HTML entities if any
    text = re.sub(r'&[a-zA-Z]+;', '', text)

    return text


def format_salary(salary_min: Optional[int], salary_max: Optional[int],
                 currency: Optional[str] = None) -> str:
    """Format salary information for display."""
    if not salary_min and not salary_max:
        return ""

    if salary_min and salary_max:
        if salary_min == salary_max:
            salary_text = f"{salary_min:,}"
        else:
            salary_text = f"{salary_min:,}-{salary_max:,}"
    elif salary_min:
        salary_text = f"от {salary_min:,}"
    elif salary_max:
        salary_text = f"до {salary_max:,}"
    else:
        return ""

    if currency:
        salary_text += f" {currency}"

    return salary_text.replace(',', ' ')


def parse_salary_from_text(salary_text: str) -> Dict[str, Optional[int]]:
    """Parse salary information from text."""
    if not salary_text:
        return {'salary_min': None, 'salary_max': None, 'currency': None}

    # Clean the text
    salary_text = clean_text(salary_text)

    # Extract currency
    currency = None
    if 'руб' in salary_text.lower():
        currency = 'RUB'
    elif 'usd' in salary_text.lower() or '$' in salary_text:
        currency = 'USD'
    elif 'eur' in salary_text.lower() or '€' in salary_text:
        currency = 'EUR'

    # Extract numbers
    numbers = re.findall(r'\d+', salary_text.replace(' ', ''))

    if not numbers:
        return {'salary_min': None, 'salary_max': None, 'currency': currency}

    # Convert to integers
    numbers = [int(num) for num in numbers]

    if len(numbers) == 1:
        return {'salary_min': numbers[0], 'salary_max': numbers[0], 'currency': currency}
    elif len(numbers) == 2:
        return {'salary_min': min(numbers), 'salary_max': max(numbers), 'currency': currency}
    else:
        return {'salary_min': min(numbers), 'salary_max': max(numbers), 'currency': currency}


def validate_vacancy_data(vacancy: Dict[str, Any]) -> bool:
    """Validate vacancy data structure."""
    required_fields = ['title', 'link']

    for field in required_fields:
        if not vacancy.get(field):
            logger.warning(f"Missing required field: {field}")
            return False

    # Validate salary data if present
    if vacancy.get('salary_min') and vacancy.get('salary_max'):
        if vacancy['salary_min'] > vacancy['salary_max']:
            logger.warning("Invalid salary range: min > max")
            return False

    return True


def normalize_location(location: str) -> str:
    """Normalize location names for consistency."""
    if not location:
        return ""

    # Common location normalizations
    normalizations = {
        'москва': 'Москва',
        'московская': 'Московская область',
        'спб': 'Санкт-Петербург',
        'питер': 'Санкт-Петербург',
        'екб': 'Екатеринбург',
        'нижний': 'Нижний Новгород',
        'ростов': 'Ростов-на-Дону',
    }

    location_lower = location.lower().strip()

    # Check for exact matches first
    if location_lower in normalizations:
        return normalizations[location_lower]

    # Check for partial matches
    for key, value in normalizations.items():
        if key in location_lower or location_lower in key:
            return value

    return location


def detect_remote_work(description: str, location: str) -> bool:
    """Detect if vacancy offers remote work."""
    if not description and not location:
        return False

    text_to_check = f"{description} {location}".lower()

    remote_indicators = [
        'удалённ', 'remote', 'дистанционн', 'без привязки к офису',
        'можно удалённо', 'удалённая работа', 'работа из дома',
        'не требуется присутствие в офисе'
    ]

    for indicator in remote_indicators:
        if indicator in text_to_check:
            return True

    return False


def calculate_salary_statistics(vacancies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate salary statistics from vacancy data."""
    salaries = []

    for vacancy in vacancies:
        if vacancy.get('salary_min') and vacancy.get('currency') == 'RUB':
            salaries.append(vacancy['salary_min'])
        elif vacancy.get('salary_max') and vacancy.get('currency') == 'RUB':
            salaries.append(vacancy['salary_max'])

    if not salaries:
        return {
            'count': 0,
            'min': None,
            'max': None,
            'average': None,
            'median': None
        }

    salaries.sort()

    return {
        'count': len(salaries),
        'min': salaries[0],
        'max': salaries[-1],
        'average': round(sum(salaries) / len(salaries)),
        'median': salaries[len(salaries) // 2]
    }


def export_to_json(vacancies: List[Dict[str, Any]], filename: str) -> bool:
    """Export vacancies to JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(vacancies, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        return False


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to integer."""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default


def create_backup_filename(original_filename: str) -> str:
    """Create backup filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = original_filename.rsplit('.', 1) if '.' in original_filename else (original_filename, '')
    return f"{name}_backup_{timestamp}.{ext}"


def is_valid_url(url: str) -> bool:
    """Check if string is a valid URL."""
    if not url:
        return False

    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return url_pattern.match(url) is not None
