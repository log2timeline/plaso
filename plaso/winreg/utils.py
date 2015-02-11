# -*- coding: utf-8 -*-
"""This file contains Windows Registry utility functions."""

from plaso.winreg import interface


def WinRegBasename(path):
  """Determines the basename for a Windows Registry path.

  Trailing key separators are igored.

  Args:
    path: a Windows registy path with \\ as the key separator.

  Returns:
     The basename (or last path segment).
  """
  # Strip trailing key separators.
  while path and path[-1] == interface.WinRegKey.PATH_SEPARATOR:
    path = path[:-1]
  if path:
    _, _, path = path.rpartition(interface.WinRegKey.PATH_SEPARATOR)
  return path

# TOOD: create a function to return the values as a dict.
# this function should replace the repeated code blocks in multiple plugins.

# TODO: create a function to extract string data from a registry value.
