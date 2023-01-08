# -*- coding: utf-8 -*-
"""This file imports Python modules that register analysis plugins."""

try:
  from plaso.analysis import bloom
except ImportError:
  pass

from plaso.analysis import browser_search
from plaso.analysis import chrome_extension
from plaso.analysis import nsrlsvr
from plaso.analysis import sessionize
from plaso.analysis import tagging
from plaso.analysis import test_memory
from plaso.analysis import unique_domains_visited
from plaso.analysis import viper
from plaso.analysis import virustotal
