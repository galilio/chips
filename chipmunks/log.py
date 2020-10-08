import logging
import sys
from logging import handlers

import chipmunks

from chipmunks import config

logger = logging.getLogger('chipmunk')

log_level = config.get('common.log_level', 'DEBUG')
logger.setLevel(logging.__dict__[log_level])

errorHandler = handlers.TimedRotatingFileHandler('error.log', when = 'M', interval = 1, backupCount = 0)
errorHandler.setLevel(logging.ERROR)

normalHandler = handlers.TimedRotatingFileHandler("normal.log", when = 'D', interval = 1, backupCount= 0)
normalHandler.setLevel(logging.INFO);

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(log_level)

logger.addHandler(errorHandler)
logger.addHandler(normalHandler)
logger.addHandler(consoleHandler)