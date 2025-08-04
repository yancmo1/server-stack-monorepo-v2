import logging
import sys
from datetime import datetime
import os
import time
import functools

def setup_logging():
    """Set up logging configuration"""
    # Create logs directory if it doesn't exist
    try:
        os.makedirs("logs", exist_ok=True)
        log_to_file = True
    except PermissionError:
        print("Warning: Cannot create logs directory, logging to console only")
        log_to_file = False
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set up root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (only if we can write to logs directory)
    if log_to_file:
        file_handler = logging.FileHandler(
            f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name):
    """Get a logger with the specified name"""
    return logging.getLogger(name)

def log_exception(logger, message, exception):
    """Log an exception with details"""
    logger.error(f"{message}: {exception}", exc_info=True)

def log_performance(func):
    """Decorator to log function performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger = get_logger(func.__module__)
        logger.info(f"{func.__name__} executed in {end_time - start_time:.2f} seconds")
        return result
    return wrapper

def log_performance_async(func):
    """Decorator to log async function performance"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        logger = get_logger(func.__module__)
        logger.info(f"{func.__name__} executed in {end_time - start_time:.2f} seconds")
        return result
    return wrapper
