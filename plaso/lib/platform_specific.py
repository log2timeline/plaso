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


def MarkWindowsFileHandleAsNoInherit(fileno):
  """Flags a file descriptor so that child processes don't inherit it.

  Args:
    fileno (int): file handle descriptor, as returned by
  """
  if msvcrt and win32api and win32con:
    os_handle = msvcrt.get_osfhandle(fileno)
    win32api.SetHandleInformation(os_handle, win32con.HANDLE_FLAG_INHERIT, 0)
    return
  raise

def OnWindows():
  """Checks if currently running on Windows."""
  if sys.platform.startswith(u'win'):
    return True

def OnLinux():
  """Checks if currently running on Linux"""
  if sys.platform.startswith(u'linux'):
    return True

def OnMacOS():
  """Checks if currently running on MacOS/OSX/Darwin"""
  if sys.platform.startswith(u'darwin'):
    return True

