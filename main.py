#!/usr/bin/env python3
"""
MarketScope - HH.ru Vacancy Scraper - Main Application Entry Point

This application provides automated collection and analysis of job vacancies from hh.ru
with a convenient graphical user interface for interaction with the system.

Author: Скрауч Владислав Игоревич
Version: 1.0.0
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from gui.main_window import run_app
except ImportError as e:
    print(f"Error importing GUI module: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)


def check_dependencies():
    """Check if all required dependencies are available."""
    required_modules = [
        'requests',
        'bs4',  # BeautifulSoup4 imports as 'bs4'
        'pandas',
        'fake_useragent'
    ]

    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print("Missing required modules:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nPlease install dependencies:")
        print("pip install -r requirements.txt")
        return False

    return True


def setup_database():
    """Initialize the database if it doesn't exist."""
    try:
        from database.db_manager import DatabaseManager

        # Test database connection
        db = DatabaseManager()
        # Database will be created automatically with tables when first accessed
        stats = db.get_statistics()
        print(f"Database initialized successfully. Current stats: {stats}")

        return True
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False


def main():
    """Main application entry point."""
    print("MarketScope - HH.ru Vacancy Scraper v1.0.0")
    print("=" * 40)

    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        sys.exit(1)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Setup database
    if not setup_database():
        print("Warning: Database setup failed, but continuing...")

    print("Starting application...")

    try:
        # Start the GUI application
        run_app()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
