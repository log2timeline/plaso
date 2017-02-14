# -*- coding: utf-8 -*-
"""This file contains the interface for syslog plugins."""

import abc

import pyparsing

from plaso.lib import errors
from plaso.parsers import plugins


class SyslogPlugin(plugins.BasePlugin):
  """The interface for syslog plugins."""
  NAME = u'syslog_plugin'
  DESCRIPTION = u''

  # The syslog 'reporter' value for syslog messages that the plugin is able to
  # parse.
  REPORTER = u''

  # Tuples of (key, grammar), where grammar is a PyParsing definition for a
  # line type that the plugin can handle. This must be defined by each plugin.
  # This is defined as a list of tuples so that more than one grammar can be
  # defined. This is so that each plugin can handle multiple types of message.
  # The tuple should have two entries, a key and a grammar. This is done to
  # keep the structures in an order of priority/preference.
  # The key is a comment or an identification that is passed to the ParseMessage
  # method so that the plugin can identify which grammar matched.
  MESSAGE_GRAMMARS = []

  @abc.abstractmethod
  def ParseMessage(self, parser_mediator, key, timestamp, tokens):
    """Parses a syslog body that matched one of the grammars the plugin defined.

    Args:
      parser_mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      key (str): name of the parsed structure.
      timestamp (int): number of micro seconds since January 1, 1970,
          00:00:00 UTC or 0 on error.
      tokens (dict[str, str]): names of the fields extracted by the syslog
          parser and the matching grammar, and values are the values of those
          fields.
    """

  def Process(self, parser_mediator, timestamp, syslog_tokens, **kwargs):
    """Processes the data structure produced by the parser.

    Args:
      parser_mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      timestamp (int): number of micro seconds since January 1, 1970,
          00:00:00 UTC or 0 on error.
      syslog_tokens (dict[str, str]): names of the fields extracted by the
          syslog parser and the matching grammar, and values are the values of
          those fields.

    Raises:
      AttributeError: If the syslog_tokens do not include a 'body' attribute.
      WrongPlugin: If the plugin is unable to parse the syslog tokens.
    """
    body = syslog_tokens.get(u'body', None)
    if not body:
      raise AttributeError(u'Missing required attribute: body')

    for key, grammar in iter(self.MESSAGE_GRAMMARS):
      try:
        tokens = grammar.parseString(body)
        syslog_tokens.update(tokens.asDict())
        self.ParseMessage(parser_mediator, key, timestamp, syslog_tokens)
        return
      except pyparsing.ParseException:
        pass

    raise errors.WrongPlugin(u'Unable to create event from: {0:s}'.format(body))
