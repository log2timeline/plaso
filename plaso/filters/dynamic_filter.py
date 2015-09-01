# -*- coding: utf-8 -*-
"""The dynamic event object filter.

The dynamic event object filter is a variant of the event object filter that
supports for selective output fields.
"""

from plaso.filters import event_filter
from plaso.filters import manager
from plaso.lib import errors
from plaso.lib import lexer


# TODO: move this to lib.lexer ?
class SelectiveLexer(lexer.Lexer):
  """A simple selective filter lexer implementation."""

  tokens = [
      lexer.Token('INITIAL', r'SELECT', '', 'FIELDS'),
      lexer.Token('FIELDS', r'(.+) WHERE ', 'SetFields', 'FILTER'),
      lexer.Token('FIELDS', r'(.+) LIMIT', 'SetFields', 'LIMIT_END'),
      lexer.Token('FIELDS', r'(.+) SEPARATED BY', 'SetFields', 'SEPARATE'),
      lexer.Token('FIELDS', r'(.+)$', 'SetFields', 'END'),
      lexer.Token('FILTER', r'(.+) SEPARATED BY', 'SetFilter', 'SEPARATE'),
      lexer.Token('FILTER', r'(.+) LIMIT', 'SetFilter', 'LIMIT_END'),
      lexer.Token('FILTER', r'(.+)$', 'SetFilter', 'END'),
      lexer.Token('SEPARATE', r' ', '', ''),  # Ignore white space here.
      lexer.Token('SEPARATE', r'LIMIT', '', 'LIMIT_END'),
      lexer.Token(
          'SEPARATE', r'[\'"]([^ \'"]+)[\'"] LIMIT', 'SetSeparator',
          'LIMIT_END'),
      lexer.Token(
          'SEPARATE', r'[\'"]([^ \'"]+)[\'"]$', 'SetSeparator', 'END'),
      lexer.Token(
          'SEPARATE', r'(.+)$', 'SetSeparator', 'END'),
      lexer.Token(
          'LIMIT_END', r'SEPARATED BY [\'"]([^\'"]+)[\'"]', 'SetSeparator', ''),
      lexer.Token('LIMIT_END', r'(.+) SEPARATED BY', 'SetLimit', 'SEPARATE'),
      lexer.Token('LIMIT_END', r'(.+)$', 'SetLimit', 'END')]

  def __init__(self, data=''):
    """Initializes the selective lexer object.

    Args:
      data: optional initial data to be processed by the lexer.
    """
    super(SelectiveLexer, self).__init__(data=data)
    self.fields = []
    self.limit = 0
    self.lex_filter = None
    self.separator = u','

  def SetFields(self, match, **unused_kwargs):
    """Set the selective fields.

    Args:
      match: the match object (instance of re.MatchObject).
    """
    text = match.group(1).lower()
    field_text, _, _ = text.partition(' from ')

    use_field_text = field_text.replace(' ', '')
    if ',' in use_field_text:
      self.fields = use_field_text.split(',')
    else:
      self.fields = [use_field_text]

  def SetFilter(self, match, **unused_kwargs):
    """Set the filter query.

    Args:
      match: the match object (instance of re.MatchObject).
    """
    filter_match = match.group(1)
    if 'LIMIT' in filter_match:
      # This only occurs in the case where we have "LIMIT X SEPARATED BY".
      self.lex_filter, _, push_back = filter_match.rpartition('LIMIT')
      self.PushBack('LIMIT {0:s} SEPARATED BY '.format(push_back))
    else:
      self.lex_filter = filter_match

  def SetLimit(self, match, **unused_kwargs):
    """Set the row limit.

    Args:
      match: the match object (instance of re.MatchObject).
    """
    try:
      limit = int(match.group(1))
    except ValueError:
      self.Error('Invalid limit value, should be int [{}] = {}'.format(
          type(match.group(1)), match.group(1)))
      limit = 0

    self.limit = limit

  def SetSeparator(self, match, **unused_kwargs):
    """Set the separator of the output, only uses the first char.

    Args:
      match: the match object (instance of re.MatchObject).
    """
    separator = match.group(1)
    if separator:
      self.separator = separator[0]


class DynamicFilter(event_filter.EventObjectFilter):
  """Event object filter that supports for selective output fields.

  This filter is essentially the same as the event object filter except it wraps
  it in a selection of which fields should be included by an output module that
  has support for selective fields. That is to say the filter:

    SELECT field_a, field_b WHERE attribute contains 'text'

  Will use the event object filter "attribute contains 'text'" and at the same
  time indicate to the appropriate output module that the user wants only the
  fields field_a and field_b to be used in the output.
  """

  _STATE_END = u'END'

  def __init__(self):
    """Initialize the selective event object filter."""
    super(DynamicFilter, self).__init__()
    self._fields = []
    self._limit = 0
    self._separator = u','

  @property
  def fields(self):
    """Set the fields property."""
    return self._fields

  @property
  def limit(self):
    """The limit of row counts."""
    return self._limit

  @property
  def separator(self):
    """The separator value."""
    return self._separator

  def CompileFilter(self, filter_expression):
    """Compiles the filter expression.

    The filter expression contains an object filter expression extended
    with selective field selection.

    Args:
      filter_expression: string that contains the filter expression.

    Raises:
      WrongPlugin: if the filter could not be compiled.
    """
    lexer_object = SelectiveLexer(filter_expression)

    lexer_object.NextToken()
    if lexer_object.error:
      raise errors.WrongPlugin(u'Malformed filter string.')

    lexer_object.NextToken()
    if lexer_object.error:
      raise errors.WrongPlugin(u'No fields defined.')

    while lexer_object.state != self._STATE_END:
      lexer_object.NextToken()
      if lexer_object.error:
        raise errors.WrongPlugin(u'No filter defined for DynamicFilter.')

    if lexer_object.state != self._STATE_END:
      raise errors.WrongPlugin(
          u'Malformed DynamicFilter, end state not reached.')

    self._fields = lexer_object.fields
    self._limit = lexer_object.limit
    self._separator = u'{0:s}'.format(lexer_object.separator)

    if lexer_object.lex_filter:
      super(DynamicFilter, self).CompileFilter(lexer_object.lex_filter)
    else:
      self._matcher = None
    self._filter_expression = filter_expression


manager.FiltersManager.RegisterFilter(DynamicFilter)
