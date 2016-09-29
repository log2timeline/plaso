# -*- coding: utf-8 -*-
"""This file contains functions for certain platform specific operations."""
import sys


# Windows-only imports
try:
  import msvcrt
  import win32api
  import win32con
except ImportError:
  msvcrt = None
  win32api = None
  win32con = None


def DisableWindowsFileHandleInheritance(file_descriptor):
  """Flags a Windows file descriptor so that child processes don't inherit it.

  Args:
    file_descriptor (int): file handle descriptor, as returned by fileno() and
        similar methods.
  """
  if msvcrt and win32api and win32con:
    os_handle = msvcrt.get_osfhandle(file_descriptor)
    win32api.SetHandleInformation(os_handle, win32con.HANDLE_FLAG_INHERIT, 0)
    return
  raise RuntimeError


def PlatformIsDarwin():
  """Checks if the current platform is Windows.

  Returns:
    bool: True if Python is running on Darwin.
  """
  return sys.platform.startswith(u'darwin')


def PlatformIsLinux():
  """Checks if the current platform is Windows.

  Returns:
    bool: True if Python is running on Windows.
  """
  return sys.platform.startswith(u'linux')


def PlatformIsWindows():
  """Checks if the current platform is Windows.

  Returns:
    bool: True if Python is running on Windows.
  """
  return sys.platform.startswith(u'win') or sys.platform.startswith(u'cygwin')
