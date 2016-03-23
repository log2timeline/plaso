# -*- coding: utf-8 -*-
"""The SAM users Windows Registry event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class SAMUsersWindowsRegistryEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a SAM users Windows Registry event."""

  DATA_TYPE = u'windows:registry:sam_users'

  FORMAT_STRING_PIECES = [
      u'[{key_path}]',
      u'Username: {username}',
      u'Full name: {fullname}',
      u'Comments: {comments}',
      u'RID: {account_rid}',
      u'Login count: {login_count}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{username}',
      u'RID: {account_rid}',
      u'Login count: {login_count}']

  SOURCE_LONG = u'Registry Key: User Account Information'
  SOURCE_SHORT = u'REG'


manager.FormattersManager.RegisterFormatter(
    SAMUsersWindowsRegistryEventFormatter)
