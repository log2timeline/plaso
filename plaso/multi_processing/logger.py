# -*- coding: utf-8 -*-
"""The multi-processing sub module logger."""

from __future__ import unicode_literals

import logging


_logger = logging.getLogger('multi_processing')

# Mimic the logging module interface.
critical = _logger.critical
debug = _logger.debug
error = _logger.error
exception = _logger.exception
info = _logger.info
log = _logger.log
warning = _logger.warning
