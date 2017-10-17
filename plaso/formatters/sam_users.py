# -*- coding: utf-8 -*-
"""The SAM users Windows Registry event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SAMUsersWindowsRegistryEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a SAM users Windows Registry event."""

  DATA_TYPE = 'windows:registry:sam_users'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Username: {username}',
      'Full name: {fullname}',
      'Comments: {comments}',
      'RID: {account_rid}',
      'Login count: {login_count}']

  FORMAT_STRING_SHORT_PIECES = [
      '{username}',
      'RID: {account_rid}',
      'Login count: {login_count}']

  SOURCE_LONG = 'Registry Key: User Account Information'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(
    SAMUsersWindowsRegistryEventFormatter)
