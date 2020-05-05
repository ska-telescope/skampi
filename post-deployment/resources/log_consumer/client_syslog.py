import logging
import logging.handlers

logger = logging.getLogger('my simple test')
logger.setLevel(logging.DEBUG)
handler = logging.handlers.SysLogHandler(address=('192.168.100.71',514))
logger.addHandler(handler)
logger.debug('This is a debug message')
logger.info('This is an info message')
logger.warning('This is a warning message')
logger.error('This is an error message')
logger.critical('This is a critical message')
