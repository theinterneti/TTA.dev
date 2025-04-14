#!/usr/bin/env python3
"""
Main entry point for the TTA.dev application.
"""

import os
import logging

# Try to import dotenv, but continue if it's not available
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        logging.warning("python-dotenv not installed, skipping .env loading")

# Configure logging
try:
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/app.log", mode="a")
        ]
    )
except Exception as e:
    # Fallback to console logging if file logging fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    logging.warning(f"Could not set up file logging: {e}")

logger = logging.getLogger(__name__)

def main():
    """Main function to start the application."""
    # Load environment variables
    load_dotenv()

    logger.info("Starting TTA.dev application...")

    # Add your application initialization code here

    logger.info("TTA.dev application started successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Error in main application: {e}")
