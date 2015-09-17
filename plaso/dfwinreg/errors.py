# -*- coding: utf-8 -*-
"""This file contains the error classes."""

class Error(Exception):
  """Base error class."""


class WinRegistryValueError(Error):
  """Raised when a Windows Registry value cannot be read."""
