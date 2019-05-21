# -*- coding: utf-8 -*-
"""Event filter expression parser."""

from __future__ import unicode_literals

import binascii
import codecs
import logging
import re

from plaso.filters import expressions
from plaso.lib import errors


class Token(object):
  """An event filter expression parser token.

  Attributes:
    actions (list[str]): list of method names in the EventFilterExpressionParser
        to call.
    next_state (str): next state we transition to if this Token matches.
    re_str (str): regular expression to try and match from the current point.
    state (str): parser state within the token should be applied or None if
        the token should be applied regardless of the parser state.
  """

  _ACTION_SEPARATOR = ','

  def __init__(self, state, regex, actions, next_state):
    """Initializes an event filter expressions parser token.

    Args:
      state (str): parser state within the token should be applied or None if
          the token should be applied regardless of the parser state.
      regex (str): regular expression to try and match from the current point.
      actions (list[str]): list of method names in the
          EventFilterExpressionParser to call.
      next_state (str): next state we transition to if this Token matches.
    """
    super(Token, self).__init__()
    self._regex = re.compile(regex, re.DOTALL | re.I | re.M | re.S | re.U)
    self.actions = []
    self.next_state = next_state
    self.state = state

    if actions:
      self.actions = actions.split(self._ACTION_SEPARATOR)

  def CompareExpression(self, expression):
    """Compares the token against an expression string.

    Args:
      expression (str): expression string.

    Returns:
      re.Match: the regular expression match object if the expression string
          matches the token or None if no match.
    """
    return self._regex.match(expression)


class EventFilterExpressionParser(object):
  """Event filter expression parser.

  Examples of valid syntax:
    size is 40
    (name contains "Program Files" AND hash.md5 is "123abc")
    @imported_modules (num_symbols = 14 AND symbol.name is "FindWindow")
  """
  _CONTINUE_STATE = 'CONTINUE'
  _INITIAL_STATE = 'INITIAL'

  _OPERATORS_WITH_NEGATION = frozenset(['contains', 'equals', 'inset', 'is'])

  _TOKENS = [
      # Operators and related tokens
      Token('INITIAL', r'\@[\w._0-9]+', 'ContextOperator,PushState',
            'CONTEXTOPEN'),
      Token('INITIAL', r'[^\s\(\)]', 'PushState,_PushBack', 'ATTRIBUTE'),
      Token('INITIAL', r'\(', 'PushState,BracketOpen', None),
      Token('INITIAL', r'\)', 'BracketClose', 'BINARY'),

      # Context
      Token('CONTEXTOPEN', r'\(', 'BracketOpen', 'INITIAL'),

      # Double quoted string
      Token('STRING', '"', 'PopState,StringFinish', None),
      Token('STRING', r'\\x(..)', 'HexEscape', None),
      Token('STRING', r'\\(.)', 'StringEscape', None),
      Token('STRING', r'[^\\"]+', 'StringInsert', None),

      # Single quoted string
      Token('SQ_STRING', '\'', 'PopState,StringFinish', None),
      Token('SQ_STRING', r'\\x(..)', 'HexEscape', None),
      Token('SQ_STRING', r'\\(.)', 'StringEscape', None),
      Token('SQ_STRING', r'[^\\\']+', 'StringInsert', None),

      # Basic expression
      Token('ATTRIBUTE', r'[\w._0-9]+', 'StoreAttribute', 'OPERATOR'),
      Token('OPERATOR', r'not ', '_NegateExpression', None),
      Token('OPERATOR', r'(\w+|[<>!=]=?)', 'StoreOperator', 'CHECKNOT'),
      Token('CHECKNOT', r'not', '_NegateExpression', 'ARG'),
      Token('CHECKNOT', r'\s+', None, None),
      Token('CHECKNOT', r'([^not])', '_PushBack', 'ARG'),
      Token('ARG', r'(\d+\.\d+)', 'InsertFloatArg', 'ARG'),
      Token('ARG', r'(0x\d+)', 'InsertInt16Arg', 'ARG'),
      Token('ARG', r'(\d+)', 'InsertIntArg', 'ARG'),
      Token('ARG', '"', 'PushState,StringStart', 'STRING'),
      Token('ARG', '\'', 'PushState,StringStart', 'SQ_STRING'),
      # When the last parameter from arg_list has been pushed

      # State where binary operators are supported (AND, OR)
      Token('BINARY', r'(?i)(and|or|\&\&|\|\|)', '_AddBinaryOperator',
            'INITIAL'),
      # - We can also skip spaces
      Token('BINARY', r'\s+', None, None),
      # - But if it's not "and" or just spaces we have to go back
      Token('BINARY', '.', '_PushBack,PopState', None),

      # Skip whitespace.
      Token(None, r'\s+', None, None)]

  def __init__(self):
    """Initializes an event filter expression parser."""
    super(EventFilterExpressionParser, self).__init__()
    self._buffer = ''
    self._current_expression = None
    self._error = 0
    self._flags = 0
    self._have_negate_keyword = False
    self._processed_buffer = ''
    self._stack = []
    self._state = self._INITIAL_STATE
    self._state_stack = []
    self._string = None

  def _AddBinaryOperator(self, string=None, **unused_kwargs):
    """Adds a binary operator to the stack.

    Args:
      string (str): operator, such as "and", "or", "&&" or "||".
    """
    expression = expressions.BinaryExpression(operator=string)
    self._stack.append(expression)

  def _CombineContext(self):
    """Combines a context expression."""
    item_index = len(self._stack) - 1
    while item_index >= 0:
      item = self._stack[item_index]
      previous_item = self._stack[item_index - 1]

      if (isinstance(previous_item, expressions.ContextExpression) and
          isinstance(item, expressions.Expression)):
        previous_item.SetExpression(item)

        self._stack.pop(item_index)
        item_index -= 1

      item_index -= 1

  def _CombineBinaryExpressions(self, operator):
    """Combines binary expressions.

    Args:
      operator (str): operator, such as "and" or "or".
    """
    operator_lower = operator.lower()

    item_index = 1
    number_of_items = len(self._stack) - 1
    while item_index < number_of_items:
      item = self._stack[item_index]
      if (isinstance(item, expressions.BinaryExpression) and
          item.operator.lower() == operator_lower):
        previous_item = self._stack[item_index - 1]
        next_item = self._stack[item_index + 1]

        if (isinstance(previous_item, expressions.Expression) and
            isinstance(next_item, expressions.Expression)):
          item.AddOperands(previous_item, next_item)

          self._stack.pop(item_index + 1)
          self._stack.pop(item_index - 1)

          item_index -= 2
          number_of_items -= 2

      item_index += 1
      if item_index == 0:
        item_index += 1

  def _CombineParenthesis(self):
    """Combines parenthesis."""
    item_index = 1
    number_of_items = len(self._stack) - 1
    while item_index < number_of_items:
      item = self._stack[item_index]
      previous_item = self._stack[item_index - 1]
      next_item = self._stack[item_index + 1]

      if (previous_item == '(' and next_item == ')' and
          isinstance(item, expressions.Expression)):
        self._stack.pop(item_index + 1)
        self._stack.pop(item_index - 1)

        item_index -= 2
        number_of_items -= 2

      item_index += 1
      if item_index == 0:
        item_index += 1

  def _GetNextToken(self):
    """Determines the next parser token based on the expression.

    Returns:
      Token: parser token or None if the buffer is empty.

    Raises:
      ParseError: if no token matched the expression.
    """
    if not self._buffer:
      return None

    supported_states = (None, self._state)
    for token in self._TOKENS:
      if token.state not in supported_states:
        continue

      match = token.CompareExpression(self._buffer)
      if not match:
        continue

      # The match consumes the data off the buffer (the handler can put it back
      # if it likes)
      match_end_offset = match.end()
      self._processed_buffer = ''.join(
          [self._processed_buffer, self._buffer[:match_end_offset]])
      self._buffer = self._buffer[match_end_offset:]

      next_state = token.next_state
      for action in token.actions:
        callback = getattr(self, action, self.Default)

        # Allow a callback to skip other callbacks.
        possible_next_state = callback(string=match.group(0), match=match)
        if possible_next_state == self._CONTINUE_STATE:
          continue

        # Override the state from the Token
        if possible_next_state:
          next_state = possible_next_state

      # Update the next state
      if next_state:
        self._state = next_state

      return token

    raise errors.ParseError((
        'No token match for parser state: {0:s} at position {1!s}: {2!s} '
        '<----> {3!s} )').format(
            self._state, len(self._processed_buffer), self._processed_buffer,
            self._buffer))

  def _NegateExpression(self, **unused_kwargs):
    """Reverses the logic of (negates) the current expression.

    Raises:
      ParseError: when the negation keyword (not) is expressed more than once,
          used after an argument or before an operator that does not support
          negation.
    """
    if self._have_negate_keyword:
      raise errors.ParseError(
          'Negation keyword (not) can only be expressed once.')

    if self._current_expression.args:
      raise errors.ParseError(
          'Negation keyword (not) cannot be used after an argument.')

    operator = self._current_expression.operator
    if operator and operator.lower() not in self._OPERATORS_WITH_NEGATION:
      raise errors.ParseError(
          'Operator: {0:s} does not support negation.'.format(operator))

    self._have_negate_keyword = True

    logging.debug('Negating expression')
    self._current_expression.Negate()

  def _PushBack(self, string='', **unused_kwargs):
    """Pushes the current expression back on the buffer.

    Args:
      string (Optional[str]): expression string.
    """
    self._buffer = ''.join([string, self._buffer])
    self._processed_buffer = self._processed_buffer[:-len(string)]

  def _Reduce(self):
    """Reduces the expression stack into a single expression.

    Returns:
      Expression: remaining expression on the stack.

    Raises:
      ParseError: if the current state is unsupported or the remaining number
          of items on the stack is not 1.
    """
    if self._state not in ('BINARY', 'INITIAL'):
      raise errors.ParseError((
          'Unsupported intial state: {0:s} - premature end of expression '
          'at position {1!s}: {2!s} <----> {3!s} )').format(
              self._state, len(self._processed_buffer), self._processed_buffer,
              self._buffer))

    number_of_items = len(self._stack)
    while number_of_items > 1:
      # Precedence order
      self._CombineParenthesis()
      self._CombineBinaryExpressions('and')
      self._CombineBinaryExpressions('or')
      self._CombineContext()

      # No change
      if len(self._stack) == number_of_items:
        break

      number_of_items = len(self._stack)

    if number_of_items != 1:
      raise errors.ParseError((
          'Unsupported event filter expression at position {0!s}: {1!s} <----> '
          '{2!s} )').format(
              len(self._processed_buffer), self._processed_buffer,
              self._buffer))

    return self._stack[0]

  def _Reset(self):
    """Resets the parser."""
    self._buffer = ''
    self._current_expression = expressions.EventExpression()
    self._error = 0
    self._flags = 0
    self._have_negate_keyword = False
    self._processed_buffer = ''
    self._stack = []
    self._state = self._INITIAL_STATE
    self._state_stack = []
    self._string = None

  def BracketClose(self, **unused_kwargs):
    """Defines a closing bracket."""
    self._stack.append(')')

  def BracketOpen(self, **unused_kwargs):
    """Defines an open bracket."""
    self._stack.append('(')

  def ContextOperator(self, string='', **unused_kwargs):
    """Sets a context operator.

    Args:
      string (str): operator.
    """
    context_expression = expressions.ContextExpression(attribute=string[1:])
    self._stack.append(context_expression)

  def Default(self, **kwarg):
    """Default callback handler."""
    logging.debug('Default handler: {0!s}'.format(kwarg))

  # pylint: disable=missing-raises-doc
  def HexEscape(self, string, match, **unused_kwargs):
    """Converts a hex escaped string.

    Raises:
      ParseError: if the string is not hex escaped.
    """
    logging.debug('HexEscape matched {0:s}.'.format(string))
    hex_string = match.group(1)
    try:
      hex_string = binascii.unhexlify(hex_string)
      hex_string = codecs.decode(hex_string, 'utf-8')
      self._string += hex_string
    except (TypeError, binascii.Error):
      raise errors.ParseError('Invalid hex escape {0!s}.'.format(hex_string))

  def InsertArg(self, string='', **unused_kwargs):
    """Inserts an argument into the current expression.

    Args:
      string (Optional[str]): argument string.

    Returns:
      str: state or None if the argument could not be added to the current
          expression.

    Raises:
      ParseError: if the operator does not support negation.
    """
    # Note that "string" is not necessarily of type string.
    logging.debug('Storing argument: {0!s}'.format(string))

    if self._have_negate_keyword:
      operator = self._current_expression.operator
      if operator and operator.lower() not in self._OPERATORS_WITH_NEGATION:
        raise errors.ParseError(
            'Operator: {0:s} does not support negation (not).'.format(operator))

    # This expression is complete
    if self._current_expression.AddArg(string):
      self._stack.append(self._current_expression)
      self._current_expression = expressions.EventExpression()
      # We go to the BINARY state, to find if there's an AND or OR operator
      return 'BINARY'

    return None

  def InsertFloatArg(self, string='', **unused_kwargs):
    """Inserts a floating-point argument into the current expression.

    Args:
      string (Optional[str]): argument string that contains a floating-point
          value.

    Returns:
      str: state or None if the argument could not be added to the current
          expression.

    Raises:
      ParseError: TBD.
    """
    try:
      float_value = float(string)
    except (TypeError, ValueError):
      raise errors.ParseError('{0:s} is not a valid float.'.format(string))
    return self.InsertArg(float_value)

  # pylint: disable=missing-raises-doc
  def InsertIntArg(self, string='', **unused_kwargs):
    """Inserts a decimal integer argument into the current expression.

    Args:
      string (Optional[str]): argument string that contains an integer value
          formatted in decimal.

    Returns:
      str: state or None if the argument could not be added to the current
          expression.

    Raises:
      ParseError: TBD.
    """
    try:
      int_value = int(string)
    except (TypeError, ValueError):
      raise errors.ParseError('{0:s} is not a valid integer.'.format(string))
    return self.InsertArg(int_value)

  # pylint: disable=missing-raises-doc
  def InsertInt16Arg(self, string='', **unused_kwargs):
    """Inserts a hexadecimal integer argument into the current expression.

    Args:
      string (Optional[str]): argument string that contains an integer value
          formatted in hexadecimal.

    Returns:
      str: state or None if the argument could not be added to the current
          expression.

    Raises:
      ParseError: TBD.
    """
    try:
      int_value = int(string, 16)
    except (TypeError, ValueError):
      raise errors.ParseError(
          '{0:s} is not a valid base16 integer.'.format(string))
    return self.InsertArg(int_value)

  def Parse(self, expression):
    """Parses an event filter expression.

    Args:
      expression (str): event filter expression.

    Returns:
      Expression: expression.
    """
    if not expression:
      return expressions.IdentityExpression()

    self._Reset()
    self._buffer = expression

    token = self._GetNextToken()
    while token:
      token = self._GetNextToken()

    return self._Reduce()

  def PopState(self, **unused_kwargs):
    """Pops the previous state from the stack.

    Returns:
      str: parser state.

    Raises:
      ParseError: if the stack is empty.
    """
    try:
      self._state = self._state_stack.pop()
    except IndexError:
      raise errors.ParseError((
          'Tried to pop state from an empty stack - possible recursion error '
          'at position {0!s}: {1!s} <----> {2!s} )').format(
              len(self._processed_buffer), self._processed_buffer,
              self._buffer))

    logging.debug('Returned state to {0:s}'.format(self._state))
    return self._state

  def PushState(self, **unused_kwargs):
    """Pushes the current state on the state stack."""
    logging.debug('Storing state {0:s}'.format(repr(self._state)))
    self._state_stack.append(self._state)

  def StringEscape(self, string='', match='', **unused_kwargs):
    """Escapes backslashes found inside an expression string.

    Backslashes followed by anything other than [\'"rnbt.ws] will raise
    an Error.

    Args:
      string (Optional[str]): expression string.
      match (Optional[re.MatchObject]): the regular expression match object,
          where match.group(1) contains the escaped code.

    Raises:
      ParseError: When the escaped string is not one of [\'"rnbt].
    """
    if match.group(1) not in '\\\'"rnbt\\.ws':
      raise errors.ParseError('Invalid escape character {0:s}.'.format(string))

    self._string += codecs.decode(string, 'unicode_escape')

  def StringFinish(self, **unused_kwargs):
    """Finishes a string operation.

    Returns:
      str: token or None when the internal state is not "ATTRIBUTE" or
          "ARG".
    """
    if self._state == 'ATTRIBUTE':
      return self.StoreAttribute(string=self._string)

    if self._state == 'ARG':
      return self.InsertArg(string=self._string)

    return None

  def StringInsert(self, string='', **unused_kwargs):
    """Adds the expression string to the internal string.

    Args:
      string (Optional[str]): expression string.
    """
    self._string += string

  def StringStart(self, **unused_kwargs):
    """Initializes the internal string."""
    self._string = ''

  # pylint: disable=missing-raises-doc
  def StoreAttribute(self, string='', **unused_kwargs):
    """Store the attribute.

    Args:
      string (Optional[str]): expression string.

    Returns:
      str: token.

    Raises:
      ParseError: TBD.
    """
    logging.debug('Storing attribute {0:s}'.format(repr(string)))

    self._have_negate_keyword = False

    # TODO: Update the expected number_of_args
    try:
      self._current_expression.SetAttribute(string)
    except AttributeError:
      raise errors.ParseError('Invalid attribute \'{0:s}\''.format(string))

    return 'OPERATOR'

  def StoreOperator(self, string='', **unused_kwargs):
    """Store the operator.

    Args:
      string (Optional[str]): expression string.
    """
    logging.debug('Storing operator {0:s}'.format(repr(string)))
    self._current_expression.SetOperator(string)
