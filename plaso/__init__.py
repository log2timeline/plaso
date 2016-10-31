# -*- coding: utf-8 -*-
"""Super timeline all the things (Plaso Langar Að Safna Öllu).

log2timeline is a tool designed to extract timestamps from various files found
on a typical computer system(s) and aggregate them. Plaso is the Python rewrite
of log2timeline.
"""

__version__ = '1.5.2'

VERSION_DEV = True
VERSION_DATE = '20161031'


def GetVersion():
  """Retrieves the version.

  Returns:
    A string containing the version.
  """
  if VERSION_DEV:
    return u'{0:s}_{1:s}'.format(__version__, VERSION_DATE)

  return __version__
