# -*- coding: utf-8 -*-
"""Formatter for the Popularity Contest parser events."""

from plaso.formatters import interface
from plaso.formatters import manager


class PopularityContestSessionFormatter(interface.ConditionalEventFormatter):
  """Formatter for Popularity Contest Session information."""

  DATA_TYPE = 'popularity_contest:session:event'

  FORMAT_STRING_PIECES = [
      u'Session {session}',
      u'{status}',
      u'ID {hostid}',
      u'[{details}]']

  FORMAT_STRING_SHORT_PIECES = [
      u'Session {session}',
      u'{status}']

  SOURCE_LONG = 'Popularity Contest Session'
  SOURCE_SHORT = 'LOG'


class PopularityContestLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for Popularity Contest Log events."""

  DATA_TYPE = 'popularity_contest:log:event'

  FORMAT_STRING_PIECES = [
      u'mru [{mru}]',
      u'package [{package}]',
      u'tag [{record_tag}]']

  FORMAT_STRING_SHORT_PIECES = [u'{mru}']

  SOURCE_LONG = 'Popularity Contest Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatters([
    PopularityContestSessionFormatter, PopularityContestLogFormatter])
