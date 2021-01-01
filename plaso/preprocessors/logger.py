# -*- coding: utf-8 -*-
"""The preprocessors sub module logger."""

import logging


_logger = logging.getLogger('preprocessors')

# Mimic the logging module interface.
critical = _logger.critical
debug = _logger.debug
error = _logger.error
exception = _logger.exception
info = _logger.info
log = _logger.log
warning = _logger.warning
