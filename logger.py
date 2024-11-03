import logging

# Configure the logger
logger = logging.getLogger("scraper_logger")
logger.setLevel(logging.DEBUG)  # Set the root logger level to DEBUG or INFO

# Create handlers for logging to info.log and error.log
info_handler = logging.FileHandler("info.log")
info_handler.setLevel(logging.INFO)  # Logs INFO and higher to info.log

error_handler = logging.FileHandler("error.log")
error_handler.setLevel(logging.ERROR)  # Logs ERROR and higher to error.log


# Create formatters and add them to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
info_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(info_handler)
logger.addHandler(error_handler)
