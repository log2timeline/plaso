# -*- coding: utf-8 -*-
"""Custom logger."""

from __future__ import unicode_literals

import gzip
import logging


class CompressedFileHandler(logging.FileHandler):
  """Compressed file handler for logging."""

  def __init__(self, filename, mode='a', encoding=None):
    """Initializes a compressed file logging handler.

    Args:
      filename (str): name of the log file.
      mode (Optional[str]): file access mode.
      encoding (Optional[str]): encoding of the log lines.
    """
    super(CompressedFileHandler, self).__init__(
        filename, mode=mode, encoding=encoding, delay=True)

  def _open(self):
    """Opens the current base file with the (original) mode and encoding.

    Returns
      file: file-like object of the resulting stream.
    """
    # The gzip module supports directly setting encoding as of Python 3.3.
    return gzip.open(self.baseFilename, self.mode)

  def emit(self, record):
    """Emits a record.

    If the stream was not opened because 'delay' was specified in the
    constructor, open it before calling the superclass's emit.

    Args:
      record (logging.LogRecord): log record.
    """
    if self.encoding:
      record = record.encode(self.encoding)

    super(CompressedFileHandler, self).emit(record)
