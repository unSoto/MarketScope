import requests
from bs4 import BeautifulSoup
import time
import re
from typing import List, Dict, Any, Optional
from fake_useragent import UserAgent
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HHParser:
    """Parser for extracting job vacancies from hh.ru."""

    def __init__(self):
        """Initialize the parser with user agent rotation."""
        self.ua = UserAgent()
        self.session = requests.Session()
        self.base_url = "https://hh.ru"

    def _get_headers(self) -> Dict[str, str]:
        """Generate headers with random user agent."""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def _make_request(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Make HTTP request with retry logic."""
        for attempt in range(max_retries):
            try:
                headers = self._get_headers()
                response = self.session.get(url, headers=headers, timeout=30)

                if response.status_code == 200:
                    return BeautifulSoup(response.text, 'html.parser')
                elif response.status_code == 429:
                    # Rate limited, wait longer
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP {response.status_code} for URL: {url}")
                    return None

            except requests.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff

        return None

    def _extract_salary_info(self, salary_text: str) -> Dict[str, Any]:
        """Extract salary information from text."""
        if not salary_text:
            return {'salary_min': None, 'salary_max': None, 'currency': None}

        # Remove extra whitespace and normalize
        salary_text = re.sub(r'\s+', ' ', salary_text.strip())

        # Extract currency
        currency = None
        if 'руб' in salary_text.lower() or '₽' in salary_text:
            currency = 'RUB'
        elif 'usd' in salary_text.lower() or '$' in salary_text:
            currency = 'USD'
        elif 'eur' in salary_text.lower() or '€' in salary_text:
            currency = 'EUR'

        # Check for "не указан" (not specified)
        if 'не указан' in salary_text.lower() or 'не указано' in salary_text.lower():
            return {'salary_min': None, 'salary_max': None, 'currency': None}

        # Extract numbers - handle spaces in numbers (like 20 000)
        numbers = re.findall(r'\d+', salary_text.replace(' ', '').replace('\u202f', '').replace('\u00a0', ''))

        if not numbers:
            return {'salary_min': None, 'salary_max': None, 'currency': currency}

        # Convert to integers
        numbers = [int(num) for num in numbers]

        # Handle different salary formats
        if len(numbers) == 1:
            # Single salary value
            return {'salary_min': numbers[0], 'salary_max': numbers[0], 'currency': currency}
        elif len(numbers) == 2:
            # Range - check if it's "from X" or "up to X" or "X-Y"
            if 'от' in salary_text.lower() or 'from' in salary_text.lower():
                return {'salary_min': numbers[0], 'salary_max': None, 'currency': currency}
            elif 'до' in salary_text.lower() or 'up to' in salary_text.lower():
                return {'salary_min': None, 'salary_max': numbers[0], 'currency': currency}
            else:
                # Regular range
                return {'salary_min': min(numbers), 'salary_max': max(numbers), 'currency': currency}
        else:
            # Multiple values, take min and max
            return {'salary_min': min(numbers), 'salary_max': max(numbers), 'currency': currency}

    def _extract_vacancy_data(self, vacancy_element) -> Optional[Dict[str, Any]]:
        """Extract data from a single vacancy element."""
        try:
            # Get vacancy link and title - try multiple selectors
            title_element = None

            # Try the original selector
            title_element = vacancy_element.find('a', {'data-qa': 'vacancy-serp__vacancy-title'})

            # Try alternative selectors if not found
            if not title_element:
                title_element = vacancy_element.find('a', {'class': 'bloko-link'})

            if not title_element:
                title_element = vacancy_element.find('a', href=True)

            if not title_element:
                return None

            title = title_element.get_text(strip=True)
            link = title_element['href']
            if link.startswith('/'):
                link = self.base_url + link
            link = link.split('?')[0]  # Remove query parameters

            # Filter out non-vacancy entries
            title_lower = title.lower()
            non_vacancy_keywords = [
                'на карте', 'подробнее', 'показать', 'скрыть', 'карта', 'список',
                'результат', 'фильтр', 'сортировка', 'страница', 'следующая',
                'предыдущая', 'обновить', 'очистить', 'сохранить', 'поделиться',
                'похожие', 'сбросить', 'применить', 'найти', 'расширенный поиск',
                'новые', 'сначала', 'по зарплате', 'по дате', 'по релевантности'
            ]

            if any(keyword in title_lower for keyword in non_vacancy_keywords):
                logger.debug(f"Filtered out non-vacancy entry: {title}")
                return None

            # Additional filtering - must have minimum content and look like a real vacancy
            if len(title.strip()) < 10 or len(title.strip()) > 200:
                logger.debug(f"Filtered out invalid title length: {title}")
                return None

            # Filter out entries that don't look like job titles
            vacancy_keywords = [
                'вакансия', 'работа', 'требуется', 'ищем', 'приглашаем',
                'разработчик', 'аналитик', 'менеджер', 'специалист', 'инженер',
                'программист', 'дизайнер', 'маркетолог', 'консультант', 'администратор'
            ]

            has_vacancy_keywords = any(keyword in title_lower for keyword in vacancy_keywords)
            if not has_vacancy_keywords and len(title.split()) < 3:
                logger.debug(f"Filtered out non-vacancy title: {title}")
                return None

            # Get company name - try multiple selectors
            company_element = None
            company_element = vacancy_element.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})
            if not company_element:
                company_element = vacancy_element.find('div', {'class': 'vacancy-serp-item__meta-info-company'})
            if not company_element:
                company_element = vacancy_element.find('a', {'class': 'bloko-link'})

            company = company_element.get_text(strip=True) if company_element else ''

            # Filter out non-company entries
            if company:
                company_lower = company.lower()
                non_company_keywords = ['карта', 'список', 'показать', 'подробнее']
                if any(keyword in company_lower for keyword in non_company_keywords):
                    company = ''

            # Get location - try multiple selectors
            location_element = None
            location_element = vacancy_element.find('div', {'data-qa': 'vacancy-serp__vacancy-address'})
            if not location_element:
                location_element = vacancy_element.find('span', {'class': 'vacancy-serp__vacancy-address'})
            if not location_element:
                location_element = vacancy_element.find('div', {'class': 'vacancy-serp__vacancy-address'})
            if not location_element:
                location_element = vacancy_element.find('span', {'class': 'bloko-text'})
            if not location_element:
                # Try to find any text that looks like a location
                all_text_elements = vacancy_element.find_all(text=re.compile(r'Москва|Санкт-Петербург|Екатеринбург|Новосибирск|Казань|Нижний|Ростов|Уфа|Краснодар|Воронеж|Пермь|Волгоград|Красноярск|Самара|Омск|Челябинск'))
                if all_text_elements:
                    location_element = all_text_elements[0].parent if all_text_elements[0].parent else all_text_elements[0]

            location = location_element.get_text(strip=True) if location_element else ''

            # Get salary information - try multiple selectors
            salary_element = None
            salary_element = vacancy_element.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'})
            if not salary_element:
                salary_element = vacancy_element.find('div', {'class': 'vacancy-serp__vacancy-compensation'})
            if not salary_element:
                salary_element = vacancy_element.find('span', {'class': 'compensation-text'})
            if not salary_element:
                salary_element = vacancy_element.find('div', {'class': 'compensation-text'})

            # If still no salary element found, try to find it by looking for salary-specific patterns
            # but avoid experience-related text
            if not salary_element:
                all_text_elements = vacancy_element.find_all(text=True)
                for text_element in all_text_elements:
                    text = text_element.strip()
                    # Look for salary patterns but exclude experience patterns
                    if (any(char.isdigit() for char in text) and
                        any(curr in text.lower() for curr in ['руб', 'usd', 'eur', '$', '€', '₽']) and
                        not any(exp in text.lower() for exp in ['опыт', 'год', 'лет', 'месяц', 'стаж', 'junior', 'middle', 'senior'])):
                        salary_element = text_element
                        break

            # If still no salary found, try a more relaxed search
            if not salary_element:
                all_text_elements = vacancy_element.find_all(text=True)
                for text_element in all_text_elements:
                    text = text_element.strip()
                    # Look for any text that contains numbers and currency symbols
                    if (any(char.isdigit() for char in text) and
                        any(curr in text.lower() for curr in ['руб', '₽']) and
                        len(text) < 50):  # Avoid long text that might be experience
                        salary_element = text_element
                        break

            # Final attempt - look for any salary-like text in the entire vacancy element
            if not salary_element:
                vacancy_text = vacancy_element.get_text()
                # Look for patterns like "от 50000 руб", "до 100000 руб", "50000-100000 руб"
                salary_patterns = [
                    r'от\s+(\d+[\d\s]*)\s*руб',
                    r'до\s+(\d+[\d\s]*)\s*руб',
                    r'(\d+[\d\s]*)\s*-\s*(\d+[\d\s]*)\s*руб',
                    r'(\d+[\d\s]*)\s*руб',
                    r'от\s+(\d+[\d\s]*)\s*₽',
                    r'до\s+(\d+[\d\s]*)\s*₽',
                    r'(\d+[\d\s]*)\s*-\s*(\d+[\d\s]*)\s*₽',
                    r'(\d+[\d\s]*)\s*₽'
                ]

                for pattern in salary_patterns:
                    matches = re.findall(pattern, vacancy_text, re.IGNORECASE)
                    if matches:
                        # Create a fake salary element with the found text
                        from bs4 import BeautifulSoup
                        fake_element = BeautifulSoup(f"<span>{matches[0]}</span>", 'html.parser')
                        salary_element = fake_element.find('span')
                        break

            # Ultimate attempt - search for any text containing salary information
            if not salary_element:
                # Look for any text that contains salary-related keywords and numbers
                salary_keywords = ['зарплата', 'доход', 'оплата', 'руб', '₽', 'salary', 'compensation']
                all_text_elements = vacancy_element.find_all(text=True)

                for text_element in all_text_elements:
                    text = text_element.strip()
                    # Check if text contains salary keywords and numbers
                    has_salary_keyword = any(keyword in text.lower() for keyword in salary_keywords)
                    has_numbers = any(char.isdigit() for char in text)

                    if has_salary_keyword and has_numbers and len(text) < 100:
                        # Create a fake salary element
                        from bs4 import BeautifulSoup
                        fake_element = BeautifulSoup(f"<span>{text}</span>", 'html.parser')
                        salary_element = fake_element.find('span')
                        break

            # Final comprehensive search - look for salary patterns in the entire vacancy text
            if not salary_element:
                vacancy_text = vacancy_element.get_text()

                # Look for salary patterns in the full text
                salary_patterns = [
                    r'(\d+[\d\s]*)\s*руб',
                    r'(\d+[\d\s]*)\s*₽',
                    r'зарплата.*?(\d+[\d\s]*)',
                    r'доход.*?(\d+[\d\s]*)',
                    r'от.*?(\d+[\d\s]*).*?руб',
                    r'до.*?(\d+[\d\s]*).*?руб',
                    r'(\d+[\d\s]*).*?-\s*(\d+[\d\s]*).*?руб',
                    r'от.*?(\d+[\d\s]*).*?₽',
                    r'до.*?(\d+[\d\s]*).*?₽',
                    r'(\d+[\d\s]*).*?-\s*(\d+[\d\s]*).*?₽',
                    r'от\s+(\d+[\d\s]*).*?руб.*?за месяц',
                    r'до\s+(\d+[\d\s]*).*?руб.*?за месяц',
                    r'(\d+[\d\s]*).*?-\s*(\d+[\d\s]*).*?руб.*?за месяц'
                ]

                for pattern in salary_patterns:
                    matches = re.findall(pattern, vacancy_text, re.IGNORECASE)
                    if matches:
                        # Use the first match found
                        salary_text = matches[0] if isinstance(matches[0], str) else str(matches[0])
                        # Create a fake salary element
                        from bs4 import BeautifulSoup
                        fake_element = BeautifulSoup(f"<span>{salary_text}</span>", 'html.parser')
                        salary_element = fake_element.find('span')
                        break

            # Ultimate search - look for salary with additional context
            if not salary_element:
                vacancy_text = vacancy_element.get_text()

                # Look for salary patterns with more context
                comprehensive_patterns = [
                    r'от\s+(\d+[\d\s]*).*?руб.*?за месяц',
                    r'до\s+(\d+[\d\s]*).*?руб.*?за месяц',
                    r'(\d+[\d\s]*).*?-\s*(\d+[\d\s]*).*?руб.*?за месяц',
                    r'от\s+(\d+[\d\s]*).*?₽.*?за месяц',
                    r'до\s+(\d+[\d\s]*).*?₽.*?за месяц',
                    r'(\d+[\d\s]*).*?-\s*(\d+[\d\s]*).*?₽.*?за месяц',
                    r'зарплата.*?от.*?(\d+[\d\s]*).*?руб',
                    r'зарплата.*?до.*?(\d+[\d\s]*).*?руб',
                    r'зарплата.*?(\d+[\d\s]*).*?-\s*(\d+[\d\s]*).*?руб',
                    r'от\s+(\d+[\d\s]*).*?руб.*?до вычета',
                    r'до\s+(\d+[\d\s]*).*?руб.*?до вычета',
                    r'(\d+[\d\s]*).*?-\s*(\d+[\d\s]*).*?руб.*?до вычета'
                ]

                for pattern in comprehensive_patterns:
                    matches = re.findall(pattern, vacancy_text, re.IGNORECASE)
                    if matches:
                        # Use the first match found
                        salary_text = matches[0] if isinstance(matches[0], str) else str(matches[0])
                        # Create a fake salary element
                        from bs4 import BeautifulSoup
                        fake_element = BeautifulSoup(f"<span>{salary_text}</span>", 'html.parser')
                        salary_element = fake_element.find('span')
                        break

            # Final attempt - look for salary patterns with even more flexibility
            if not salary_element:
                vacancy_text = vacancy_element.get_text()

                # Debug: Log the vacancy text to see what we're working with
                logger.debug(f"Vacancy text for salary search: {vacancy_text[:200]}...")

                # Look for salary patterns with maximum flexibility
                flexible_patterns = [
                    r'от\s+(\d+[\d\s]*).*?руб',
                    r'до\s+(\d+[\d\s]*).*?руб',
                    r'(\d+[\d\s]*).*?-\s*(\d+[\d\s]*).*?руб',
                    r'от\s+(\d+[\d\s]*).*?₽',
                    r'до\s+(\d+[\d\s]*).*?₽',
                    r'(\d+[\d\s]*).*?-\s*(\d+[\d\s]*).*?₽',
                    r'зарплата.*?(\d+[\d\s]*)',
                    r'доход.*?(\d+[\d\s]*)',
                    r'оплата.*?(\d+[\d\s]*)'
                ]

                for pattern in flexible_patterns:
                    matches = re.findall(pattern, vacancy_text, re.IGNORECASE)
                    if matches:
                        logger.debug(f"Found salary match with pattern {pattern}: {matches[0]}")
                        # Use the first match found
                        salary_text = matches[0] if isinstance(matches[0], str) else str(matches[0])
                        # Create a fake salary element
                        from bs4 import BeautifulSoup
                        fake_element = BeautifulSoup(f"<span>{salary_text}</span>", 'html.parser')
                        salary_element = fake_element.find('span')
                        break

            # Last resort - look for any salary-like text in the entire vacancy
            if not salary_element:
                vacancy_text = vacancy_element.get_text()

                # Look for any text that contains salary information
                lines = vacancy_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if (any(char.isdigit() for char in line) and
                        any(curr in line.lower() for curr in ['руб', '₽']) and
                        len(line) < 100):
                        logger.debug(f"Found salary in line: {line}")
                        # Create a fake salary element
                        from bs4 import BeautifulSoup
                        fake_element = BeautifulSoup(f"<span>{line}</span>", 'html.parser')
                        salary_element = fake_element.find('span')
                        break

            # Final attempt - search for the specific format mentioned by user
            if not salary_element:
                vacancy_text = vacancy_element.get_text()

                # Specific pattern for "от 300 000 ₽ за месяц, до вычета налогов"
                specific_patterns = [
                    r'от\s+(\d+[\d\s]*).*?₽.*?за месяц.*?до вычета',
                    r'до\s+(\d+[\d\s]*).*?₽.*?за месяц.*?до вычета',
                    r'(\d+[\d\s]*).*?-\s*(\d+[\d\s]*).*?₽.*?за месяц.*?до вычета',
                    r'от\s+(\d+[\d\s]*).*?руб.*?за месяц.*?до вычета',
                    r'до\s+(\d+[\d\s]*).*?руб.*?за месяц.*?до вычета',
                    r'(\d+[\d\s]*).*?-\s*(\d+[\d\s]*).*?руб.*?за месяц.*?до вычета'
                ]

                for pattern in specific_patterns:
                    matches = re.findall(pattern, vacancy_text, re.IGNORECASE)
                    if matches:
                        logger.debug(f"Found salary with specific pattern {pattern}: {matches[0]}")
                        # Use the first match found
                        salary_text = matches[0] if isinstance(matches[0], str) else str(matches[0])
                        # Create a fake salary element
                        from bs4 import BeautifulSoup
                        fake_element = BeautifulSoup(f"<span>{salary_text}</span>", 'html.parser')
                        salary_element = fake_element.find('span')
                        break

            salary_info = self._extract_salary_info(salary_element.get_text(strip=True) if salary_element else '')

            # Get experience - try multiple selectors
            experience_element = None
            experience_element = vacancy_element.find('div', {'data-qa': 'vacancy-serp__vacancy-work-experience'})
            if not experience_element:
                experience_element = vacancy_element.find('span', string=re.compile(r'опыт|лет'))
            if not experience_element:
                experience_element = vacancy_element.find('div', {'class': 'vacancy-serp__vacancy-work-experience'})
            if not experience_element:
                # Look for experience text in any element
                experience_patterns = [
                    r'без опыта', r'опыт от', r'от 1 года', r'от 2 лет', r'от 3 лет',
                    r'от 4 лет', r'от 5 лет', r'от 6 лет', r'1-3 года', r'3-6 лет',
                    r'более 6', r'junior', r'middle', r'senior'
                ]
                for pattern in experience_patterns:
                    experience_element = vacancy_element.find(text=re.compile(pattern, re.IGNORECASE))
                    if experience_element:
                        break

            experience = experience_element.get_text(strip=True) if experience_element else ''

            # Check if remote work is mentioned - try multiple approaches
            remote_text = f"{title} {company} {location} {experience}".lower()
            remote_keywords = [
                'удалённо', 'удалённая', 'remote', 'удалён', 'дистанционно',
                'дистанционная', 'home office', 'work from home', 'wfh',
                'можно удалённо', 'удалёнка', 'удалённая работа', 'удаленная',
                'удаленный', 'удалённая работа', 'удалённый', 'удалённая работа',
                'дистанционн', 'удал', 'remote work', 'telework', 'telecommute'
            ]

            remote = any(keyword in remote_text for keyword in remote_keywords)

            # Also check for remote work indicators in the vacancy element text
            if not remote:
                all_text = vacancy_element.get_text().lower()
                remote = any(keyword in all_text for keyword in remote_keywords)

            # Get key skills (this might require visiting the individual vacancy page)
            key_skills = []

            return {
                'title': title,
                'company': company,
                'location': location,
                'experience': experience,
                'remote': remote,
                'link': link,
                **salary_info,
                'key_skills': key_skills
            }

        except Exception as e:
            logger.error(f"Error extracting vacancy data: {e}")
            return None

    def search_vacancies(self, keyword: str, location: str = None,
                        experience: str = None, max_pages: int = 10) -> List[Dict[str, Any]]:
        """Search for vacancies with given parameters."""
        vacancies = []

        # Build search URL
        search_params = {
            'text': keyword,
            'search_field': 'name',
            'items_on_page': '50'
        }

        if location:
            search_params['area'] = self._get_area_id(location)
        if experience:
            search_params['experience'] = experience

        base_search_url = f"{self.base_url}/search/vacancy"

        for page in range(max_pages):
            try:
                # Add page parameter
                params = search_params.copy()
                if page > 0:
                    params['page'] = page

                # Build URL with parameters
                query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                url = f"{base_search_url}?{query_string}"

                logger.info(f"Parsing page {page + 1}: {url}")
                soup = self._make_request(url)

                if not soup:
                    logger.error(f"Failed to load page {page + 1}")
                    break

                # Debug: Log page title and some content to verify we're getting the right page
                page_title = soup.find('title')
                if page_title:
                    logger.info(f"Page title: {page_title.get_text(strip=True)}")

                # Debug: Check if we can find any vacancy-related elements
                title_elements = soup.find_all('a', {'data-qa': 'vacancy-serp__vacancy-title'})
                logger.info(f"Found {len(title_elements)} vacancy title elements")

                # Try alternative selectors for titles
                if len(title_elements) == 0:
                    title_elements = soup.find_all('a', {'class': 'bloko-link'})
                    logger.info(f"Found {len(title_elements)} bloko-link title elements")

                if len(title_elements) == 0:
                    title_elements = soup.find_all('a', href=re.compile(r'/vacancy/'))
                    logger.info(f"Found {len(title_elements)} href vacancy title elements")

                # Find all vacancy elements - try multiple selectors
                vacancy_elements = []

                # Try the main vacancy container class
                vacancy_elements = soup.find_all('div', {'class': 'vacancy-serp-item'})

                # If not found, try alternative selectors
                if not vacancy_elements:
                    vacancy_elements = soup.find_all('div', {'data-qa': 'vacancy-serp__vacancy'})

                if not vacancy_elements:
                    vacancy_elements = soup.find_all('div', {'class': 'serp-item'})

                if not vacancy_elements:
                    # Try to find any div that contains vacancy information
                    all_divs = soup.find_all('div')
                    for div in all_divs:
                        if div.find('a', {'data-qa': 'vacancy-serp__vacancy-title'}):
                            vacancy_elements.append(div)

                if not vacancy_elements:
                    # Try even more flexible approach - look for any div with vacancy-related content
                    all_divs = soup.find_all('div')
                    for div in all_divs:
                        # Check if this div contains any link that looks like a vacancy
                        links = div.find_all('a', href=re.compile(r'/vacancy/'))
                        if links:
                            vacancy_elements.append(div)

                if not vacancy_elements:
                    # Last resort - look for any element containing job-related keywords
                    all_divs = soup.find_all('div')
                    for div in all_divs:
                        text = div.get_text().lower()
                        if any(keyword in text for keyword in ['вакансия', 'работа', 'зарплата', 'компания']):
                            vacancy_elements.append(div)

                logger.info(f"Found {len(vacancy_elements)} vacancy elements on page {page + 1}")

                # Check if this page has vacancies
                if not vacancy_elements:
                    logger.info(f"No vacancy containers found on page {page + 1}")

                    # Check if there are more pages by looking for pagination
                    pagination = soup.find('div', {'data-qa': 'pager-block'})
                    if pagination:
                        next_button = pagination.find('a', {'data-qa': 'pager-next'})
                        if not next_button or 'disabled' in next_button.get('class', []):
                            logger.info("No more pages available, stopping search")
                            break
                        else:
                            logger.info("More pages available, continuing...")
                    else:
                        logger.info("No pagination found, stopping search")
                        break
                else:
                    # Check if we should continue to next page
                    pagination = soup.find('div', {'data-qa': 'pager-block'})
                    if pagination:
                        next_button = pagination.find('a', {'data-qa': 'pager-next'})
                        if not next_button or 'disabled' in next_button.get('class', []):
                            logger.info("Reached last page, stopping search")
                            break

                # Extract data from each vacancy
                for i, element in enumerate(vacancy_elements):
                    vacancy_data = self._extract_vacancy_data(element)
                    if vacancy_data:
                        vacancies.append(vacancy_data)
                        logger.debug(f"Extracted vacancy {i+1}: {vacancy_data.get('title', 'No title')}")
                    else:
                        logger.debug(f"Failed to extract data from vacancy element {i+1}")

                # Add delay between requests to be respectful
                if page < max_pages - 1:
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error parsing page {page + 1}: {e}")
                break

        # Remove duplicates based on title and company
        unique_vacancies = []
        seen = set()

        for vacancy in vacancies:
            # Create a unique identifier based on title and company
            identifier = f"{vacancy.get('title', '')}_{vacancy.get('company', '')}_{vacancy.get('link', '')}"

            if identifier not in seen:
                seen.add(identifier)
                unique_vacancies.append(vacancy)

        logger.info(f"Total vacancies found: {len(vacancies)} (removed {len(vacancies) - len(unique_vacancies)} duplicates)")
        return unique_vacancies

    def _get_area_id(self, location: str) -> str:
        """Get area ID for location (simplified mapping)."""
        # This is a simplified mapping. In a real application,
        # you might want to fetch this from hh.ru API
        location_mapping = {
            'москва': '1',
            'московская область': '2019',
            'санкт-петербург': '2',
            'екатеринбург': '3',
            'новосибирск': '4',
            'краснодар': '53',
            'нижний новгород': '66',
            'казань': '88',
            'челябинск': '104',
            'омск': '68',
            'самара': '78',
            'ростов-на-дону': '76',
            'уфа': '99',
            'красноярск': '54',
            'воронеж': '26',
            'волгоград': '24',
            'пермь': '72'
        }

        # Try exact match first
        if location.lower() in location_mapping:
            return location_mapping[location.lower()]

        # Try partial match
        for city, area_id in location_mapping.items():
            if city in location.lower() or location.lower() in city:
                return area_id

        # Default to Russia (113) if no match found
        return '113'

    def get_detailed_vacancy_info(self, vacancy_url: str) -> Dict[str, Any]:
        """Get detailed information about a specific vacancy."""
        try:
            soup = self._make_request(vacancy_url)
            if not soup:
                return {}

            # Extract key skills
            key_skills = []
            skills_elements = soup.find_all('div', {'data-qa': 'skills-element'})
            for skill_element in skills_elements:
                skill_text = skill_element.get_text(strip=True)
                if skill_text:
                    key_skills.append(skill_text)

            # Extract description (first few paragraphs)
            description_element = soup.find('div', {'data-qa': 'vacancy-description'})
            description = ''
            if description_element:
                paragraphs = description_element.find_all('p')
                description = ' '.join([p.get_text(strip=True) for p in paragraphs[:3]])

            return {
                'key_skills': key_skills,
                'description': description
            }

        except Exception as e:
            logger.error(f"Error getting detailed vacancy info: {e}")
            return {}
