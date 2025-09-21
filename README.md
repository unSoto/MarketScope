<div align="center">

# 🏢 MarketScope - HH.ru Vacancy Scraper

![Preview](static/preview.png)

*A program for automated collection and analysis of job vacancy data from hh.ru with a convenient graphical interface*

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-Educational%20%26%20Personal%20Use%20Only-orange.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-purple.svg)](https://github.com)
[![hh.ru](https://img.shields.io/badge/hh.ru-Scraping%20Tool-yellow.svg)](https://hh.ru)

</div>

## Description

This program allows you to:
- Automatically collect job vacancies from hh.ru according to specified parameters
- Save data to a local SQLite database
- View and filter results in a convenient interface
- Export data to various formats (CSV, Excel, JSON)
- Analyze vacancy statistics

## ✨ Features

### 🎯 **Smart Job Search**
- Search by keywords, location, and experience level
- Support for all major Russian cities
- Advanced filtering options
- Real-time progress tracking

### 📊 **Data Analysis**
- Comprehensive statistics and analytics
- Salary range analysis
- Location-based insights
- Experience level distribution
- Remote work opportunities tracking

### 💾 **Data Management**
- Local SQLite database storage
- Batch data processing
- Data export to multiple formats
- Search history tracking
- Duplicate detection and removal

### 🖥️ **User-Friendly Interface**
- Modern GUI built with tkinter
- Intuitive search parameters
- Interactive results table
- Export functionality
- Real-time status updates

### 🔧 **Developer-Friendly**
- Clean, modular code structure
- Comprehensive documentation
- Type hints and docstrings
- Error handling and logging
- Configuration management

## Project Architecture

### Project Structure
```
MarketScope/
├── main.py                 # Main application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── README.md              # Documentation
├── database/              # Database module
│   ├── __init__.py
│   └── db_manager.py      # SQLite database management
├── parser/                # Parsing module
│   ├── __init__.py
│   └── hh_parser.py       # Parser for hh.ru
├── gui/                   # Graphical interface
│   ├── __init__.py
│   └── main_window.py     # Main application window
└── utils/                 # Utility functions
    ├── __init__.py
    └── helpers.py        # Helper functions
```

### Modules

#### Main Module (`main.py`)
- Application entry point
- Dependency checking
- Database initialization
- GUI launch

#### Database Module (`database/db_manager.py`)
- SQLite database management
- Table creation and migration
- CRUD operations for vacancies
- Search and filtering functionality
- Statistics collection

#### Parser Module (`parser/hh_parser.py`)
- HTTP client for hh.ru
- HTML page parsing
- Vacancy data extraction
- Pagination handling
- Restriction bypass (user-agent rotation, delays)

#### Graphical Interface (`gui/main_window.py`)
- Main application window using tkinter
- Input fields for search parameters
- Results table
- Export buttons
- Status bar and notifications

#### Configuration (`config.py`)
- Application settings
- Location and experience mapping
- Parsing parameters
- GUI settings

#### Utilities (`utils/helpers.py`)
- Helper functions
- Data validation
- Salary formatting
- Text normalization

## Database

### Vacancies Table Structure
```sql
CREATE TABLE vacancies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,                    -- Job vacancy title
    salary_min INTEGER,                     -- Minimum salary
    salary_max INTEGER,                     -- Maximum salary
    currency TEXT,                          -- Currency
    location TEXT,                          -- Location
    experience TEXT,                        -- Required experience
    key_skills TEXT,                        -- Key skills (JSON)
    company TEXT,                           -- Company
    link TEXT UNIQUE NOT NULL,              -- Vacancy link
    remote BOOLEAN DEFAULT FALSE,           -- Remote work
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Installation and Launch

### Requirements
- Python 3.7+
- pip (Python package manager)
- Internet connection (for downloading dependencies and scraping hh.ru)

### Quick Start
1. **Clone or download** the project files
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python main.py
   ```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

**Note**: sqlite3 and tkinter are part of the standard Python library and do not require separate installation.

### Running the Program
```bash
python main.py
```

### First Launch
- The program will automatically create a SQLite database (`vacancies.db`)
- Initial setup may take a few seconds
- The main window will appear with search options

## Usage

### Main Features

1. **Job Search**
   - Enter a keyword in the "Keyword" field
   - Select location from the dropdown list
   - Specify required work experience
   - Click "Start Search"

2. **Viewing Results**
   - Results are displayed in a table
   - Sorting and scrolling available
   - Double-click on a vacancy opens it in the browser

3. **Data Export**
   - File → Export to Excel
   - File → Export to CSV
   - Data is saved with a timestamp

4. **Statistics**
   - View → Statistics
   - Shows general information about collected data

### Search Parameters

- **Keyword**: Required field for job search
- **Location**: City or region (optional)
- **Work Experience**: Required experience level (optional)
  - No experience
  - 1 to 3 years
  - 3 to 6 years
  - More than 6 years

## Configuration

The main settings are located in the `config.py` file:

- `DATABASE_PATH`: Path to the database file
- `DEFAULT_PAGE_LIMIT`: Number of pages for parsing
- `REQUEST_TIMEOUT`: HTTP request timeout
- `DELAY_BETWEEN_REQUESTS`: Delay between requests
- `LOCATION_MAPPING`: Mapping of city names to hh.ru IDs

## Security and Ethics

- The program uses User-Agent rotation to avoid blocking
- Delays between requests are implemented to comply with site rules
- Does not collect users' personal data
- Works only with publicly available information

## Possible Problems

### Module Import Error
```bash
pip install -r requirements.txt
```

### Database Locked
Close all program instances and delete the `vacancies.db.lock` file

### Site hh.ru Blocks Requests
- Increase the delay between requests in config.py
- Use VPN if necessary
- Check request limits

## Development

### Adding New Features
1. Create a new branch: `git checkout -b feature/new-feature`
2. Implement the functionality
3. Add tests
4. Create a Pull Request

### Code Structure
- Use type hints
- Add docstrings
- Follow PEP 8
- Separate logic into modules

## License

**⚠️ EDUCATIONAL AND PERSONAL USE ONLY**

This project is licensed under the **MarketScope Usage License** - see the [LICENSE](LICENSE) file for full details.

### Key Points:
- ✅ **Educational Use**: Study the code, learn web scraping techniques
- ✅ **Personal Use**: Job searching for personal employment
- ✅ **Code Analysis**: Understand software architecture and Python patterns
- ❌ **Commercial Use**: Prohibited without explicit written permission
- ❌ **Mass Data Collection**: Prohibited to avoid overloading hh.ru servers
- ❌ **Service Abuse**: Must respect hh.ru's Terms of Service and robots.txt

### Important Legal Notice:
This software scrapes data from hh.ru (HeadHunter), a commercial job search platform. Users **must**:
- Comply with hh.ru's Terms of Service
- Respect their robots.txt file
- Follow reasonable request rates
- Not interfere with hh.ru's normal operations

**Violation of hh.ru's terms may result in account suspension or legal action from hh.ru.**

## Support

If you encounter problems:
1. Check the logs in the `vacancy_scraper.log` file
2. Make sure all dependencies are installed: `pip install -r requirements.txt`
3. Check your internet connection
4. Ensure you're complying with hh.ru's Terms of Service
5. Refer to the hh.ru robots.txt file for scraping guidelines

### Getting Help:
- **Email**: skrauch@example.com
- **GitHub**: github.com/skrauch
- **LinkedIn**: linkedin.com/in/skrauch

---

<div align="center">

## 👨‍💻 Developer

![Signature](static/signature.png)

**Skrauch Vladislav Igorevich**

📧 Email: vlskrauch@mail.ru
🌐 Email: @worksoto

---

**Version**: 1.0.0
**Date**: 2025
**Developer**: Skrauch Vladislav Igorevich

</div>
