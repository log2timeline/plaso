# -*- coding: utf-8 -*-
"""A parser for event filter expressions.

The parser is based on the lexer from the GRR project:
https://github.com/google/grr
"""

from __future__ import unicode_literals

import abc
import logging
import re

from plaso.lib import errors


class Token(object):
  """An event filter parser token.

  Attributes:
    actions (list[str]): list of method names in the SearchParser to call.
    next_state (str): next state we transition to if this Token matches.
    re_str (str): regular expression to try and match from the current point.
    regex (_sre.SRE_Pattern): regular expression to try and match from
        the current point.
    state_regex (str): regular expression that is considered when the current
        state matches this rule.
  """

  def __init__(self, state_regex, regex, actions, next_state, flags=re.I):
    """Initializes an event filter expressions parser token.

    Args:
      state_regex (str): regular expression that is considered when the current
          state matches this rule.
      regex (str): regular expression to try and match from the current point.
      actions (list[str]): list of method names in the SearchParser to call.
      next_state (str): next state we transition to if this Token matches.
      flags (Optional[int]): flags for the regular expression module (re).
    """
    super(Token, self).__init__()
    self.actions = []
    self.next_state = next_state
    self.re_str = regex
    self.regex = re.compile(regex, re.DOTALL | re.M | re.S | re.U | flags)
    self.state_regex = re.compile(
        state_regex, re.DOTALL | re.M | re.S | re.U | flags)

    if actions:
      self.actions = actions.split(',')


class Expression(object):
  """An event filter parser expression.

  Attributes:
    attribute (str): attribute or None if not set.
    args (list[str]): arguments.
    number_of_args (int): expected number of arguments.
    operator (str): operator or None if not set.
  """

  _NUMBER_OF_ARGS = 1

  # TODO: this currently needs to be a class attribute for objectfilter.
  # See if this can be changed to an instance attribute.
  attribute = None

  def __init__(self):
    """Initializes an event filter parser expression."""
    super(Expression, self).__init__()
    self.args = []
    self.number_of_args = 1
    self.operator = None

  def AddArg(self, argument):
    """Adds a new argument to this expression.

    Args:
       argument (str): argument to add.

    Returns:
      bool: True if the argument is the last argument, False otherwise.

    Raises:
      ParseError: If there are too many arguments.
    """
    self.args.append(argument)
    if len(self.args) > self.number_of_args:
      raise errors.ParseError('Too many arguments for this expression.')

    elif len(self.args) == self.number_of_args:
      return True

    return False

  @abc.abstractmethod
  def Compile(self, filter_implementation):
    """Given a filter implementation, compile this expression.

    Args:
      filter_implementation (type): class of the filter object, which should
          be a subclass of objectfilter.BaseFilterImplementation.

    Returns:
      object: filter object of the binary expression.
    """

  def SetAttribute(self, attribute):
    """Sets the attribute.

    Args:
      attribute (str): attribute, or None if not set.
    """
    self.attribute = attribute

  def SetOperator(self, operator):
    """Set the operator.

    Args:
      operator (str): operator, such as "and" or "&&", or None if not set.
    """
    self.operator = operator


class BinaryExpression(Expression):
  """An event filter parser expression which takes two other expressions."""

  def __init__(self, operator='', part=None):
    """Initializes an event filter parser binary expression.

    Args:
      operator (str): operator, such as "and" or "&&".
      part (str): expression part.
    """
    super(BinaryExpression, self).__init__()
    self.args = []
    self.operator = operator

    if part:
      self.args.append(part)

  def AddOperands(self, lhs, rhs):
    """Adds an operand.

    Args:
      lhs (Expression): left hand side expression.
      rhs (Expression): right hand side expression.

    Raises:
      ParseError: if either left hand side or right hand side expression
          is not an instance of Expression.
    """
    if not isinstance(lhs, Expression):
      raise errors.ParseError('Left hand side is not an expression')

    if not isinstance(rhs, Expression):
      raise errors.ParseError('Right hand side is not an expression')

    self.args = [lhs, rhs]

  def Compile(self, filter_implementation):
    """Compiles the binary expression into a filter object.

    Args:
      filter_implementation (type): class of the filter object, which should
          be a subclass of objectfilter.BaseFilterImplementation.

    Returns:
      object: filter object of the binary expression.
    """
    operator = self.operator.lower()
    if operator in ('and', '&&'):
      method = 'AndFilter'
    elif operator in ('or', '||'):
      method = 'OrFilter'
    else:
      raise errors.ParseError(
          'Invalid binary operator {0:s}'.format(operator))

    args = [x.Compile(filter_implementation) for x in self.args]
    return getattr(filter_implementation, method)(*args)


class IdentityExpression(Expression):
  """An event filter parser expression which always evaluates to True."""

  def Compile(self, filter_implementation):
    """Compiles the binary expression into a filter object.

    Args:
      filter_implementation (type): class of the filter object, which should
          be a subclass of objectfilter.BaseFilterImplementation.

    Returns:
      object: filter object of the identity expression.
    """
    return filter_implementation.IdentityFilter()


class SearchParser(object):
  """A parser for event filter expressions.

  Examples of valid syntax:
    filename contains "foo" and (size > 100k or date before "2011-10")
    date between 2011 and 2010
    files older than 1 year

  Attributes:
    buffer (str): buffer that holds the expression.
    current_expression (Expression): current expression.
    error (int): ???
    filter_string (str): ???
    flags (int): ???
    processed (int): ???
    processed_buffer (str): buffer that holds the part of the expression
        that has been processed.
    stack (list[str]): token stack.
    state (str): parser state.
    state_stack (list[str]): stack of parser states.
    string (str): string expression or None if not set.
  """
  _CONTINUE_STATE = 'CONTINUE'
  _INITIAL_STATE = 'INITIAL'

  _ERROR_TOKEN = 'Error'

  # Classes of the expressions generated by the parser.
  expression_cls = Expression
  binary_expression_cls = BinaryExpression

  # A list of Token() instances.
  tokens = [
      # Double quoted string
      Token('STRING', '"', 'PopState,StringFinish', None),
      Token('STRING', r'\\(.)', 'StringEscape', None),
      Token('STRING', r'[^\\"]+', 'StringInsert', None),

      # Single quoted string
      Token('SQ_STRING', '\'', 'PopState,StringFinish', None),
      Token('SQ_STRING', r'\\(.)', 'StringEscape', None),
      Token('SQ_STRING', r'[^\\\']+', 'StringInsert', None),

      # TODO: Implement a unary not operator.
      # The first thing we see in the initial state takes up to the ATTRIBUTE
      Token('INITIAL', r'(and|or|\&\&|\|\|)', 'BinaryOperator', None),
      Token('INITIAL', r'[^\s\(\)]', 'PushState,PushBack', 'ATTRIBUTE'),
      Token('INITIAL', r'\(', 'BracketOpen', None),
      Token('INITIAL', r'\)', 'BracketClose', None),

      Token('ATTRIBUTE', r'[\w._0-9]+', 'StoreAttribute', 'OPERATOR'),
      Token('OPERATOR', r'[a-z0-9<>=\-\+\!\^\&%]+', 'StoreOperator',
            'ARG_LIST'),
      Token('OPERATOR', r'(!=|[<>=])', 'StoreSpecialOperator', 'ARG_LIST'),
      Token('ARG_LIST', r'[^\s\'"]+', 'InsertArg', None),

      # Start a string.
      Token('.', '"', 'PushState,StringStart', 'STRING'),
      Token('.', '\'', 'PushState,StringStart', 'SQ_STRING'),

      # Skip whitespace.
      Token('.', r'\s+', None, None)]

  def __init__(self, data=''):
    """Initializes a search parser.

    Args:
      data (str): initial data to be processed by the lexer.
    """
    super(SearchParser, self).__init__()
    self.buffer = data
    self.current_expression = self.expression_cls()
    self.error = 0
    self.filter_string = data
    self.flags = 0
    self.processed = 0
    self.processed_buffer = ''
    self.stack = []
    self.state = self._INITIAL_STATE
    self.state_stack = []
    self.string = None

  def _CombineBinaryExpressions(self, operator):
    """Combines binary expressions.

    Args:
      operator (str): operator, such as "and" or "&&".
    """
    for i in range(1, len(self.stack)-1):
      item = self.stack[i]
      if (isinstance(item, BinaryExpression) and item.operator == operator and
          isinstance(self.stack[i-1], Expression) and
          isinstance(self.stack[i+1], Expression)):
        lhs = self.stack[i-1]
        rhs = self.stack[i+1]

        self.stack[i].AddOperands(lhs, rhs)
        self.stack[i-1] = None
        self.stack[i+1] = None

    self.stack = list(filter(None, self.stack))

  def _CombineParenthesis(self):
    """Combines parenthesis."""
    for i in range(len(self.stack)-2):
      if (self.stack[i] == '(' and self.stack[i+2] == ')' and
          isinstance(self.stack[i+1], Expression)):
        self.stack[i] = None
        self.stack[i+2] = None

    self.stack = list(filter(None, self.stack))

  def BinaryOperator(self, string=None, **unused_kwargs):
    """Sets the binary operator.

    Args:
      string (str): operator, such as "and" or "&&".
    """
    expression = self.binary_expression_cls(operator=string)
    self.stack.append(expression)

  def BracketClose(self, **unused_kwargs):
    """Defines a closing bracket."""
    self.stack.append(')')

  def BracketOpen(self, **unused_kwargs):
    """Defines an open bracket."""
    self.stack.append('(')

  def Close(self):
    """Forces parse the remaining data in the buffer."""
    while self.NextToken():
      if not self.buffer:
        return

  def Default(self, **kwarg):
    """Default callback handler."""
    logging.debug('Default handler: {0!s}'.format(kwarg))

  def Empty(self):
    """Checks if the buffer is empty.

    Returns:
      bool: True if the buffer is emtpy.
    """
    return not self.buffer

  def Error(self, message=None, weight=1):  # pylint: disable=unused-argument
    """Raises a parse error.

    Args:
      message (Optional[str]): error message.
      weight (Optional[int]): error weight.

    Raises:
      ParseError: always raised.
    """
    raise errors.ParseError(
        '{0:s} in position {1:d}: {2:s} <----> {3:s} )'.format(
            message, len(self.processed_buffer), self.processed_buffer,
            self.buffer))

  def Feed(self, data):
    """Feeds the buffer with data.

    Args:
      data (str): data to be processed by the search parser.
    """
    self.buffer = ''.join([self.buffer, data])

  def InsertArg(self, string='', **unused_kwargs):
    """Inserts an argument into the current expression.

    Args:
      string (Optional[str]): argument string.

    Returns:
      str: state.
    """
    logging.debug('Storing Argument {0:s}'.format(string))

    # This expression is complete
    if self.current_expression.AddArg(string):
      self.stack.append(self.current_expression)
      self.current_expression = self.expression_cls()
      return self.PopState()

    return None

  def NextToken(self):
    """Fetches the next token by trying to match any of the regexes in order.

    Returns:
      str: token.
    """
    current_state = self.state
    for token in self.tokens:
      # Does the rule apply to us?
      if not token.state_regex.match(current_state):
        continue

      # Try to match the rule
      m = token.regex.match(self.buffer)
      if not m:
        continue

      # The match consumes the data off the buffer (the handler can put it back
      # if it likes)
      # TODO: using joins might be more efficient here.
      self.processed_buffer += self.buffer[:m.end()]
      self.buffer = self.buffer[m.end():]
      self.processed += m.end()

      next_state = token.next_state
      for action in token.actions:

        # Is there a callback to handle this action?
        callback = getattr(self, action, self.Default)

        # Allow a callback to skip other callbacks.
        try:
          possible_next_state = callback(string=m.group(0), match=m)
          if possible_next_state == self._CONTINUE_STATE:
            continue
          # Override the state from the Token
          elif possible_next_state:
            next_state = possible_next_state
        except errors.ParseError as exception:
          self.Error(exception)

      # Update the next state
      if next_state:
        self.state = next_state

      return token

    # Check that we are making progress - if we are too full, we assume we are
    # stuck.
    self.Error('Expected {0:s}'.format(self.state))
    self.processed_buffer += self.buffer[:1]
    self.buffer = self.buffer[1:]
    return self._ERROR_TOKEN

  def Parse(self):
    """Parses the data in the internal buffer.

    Returns:
      Expression: expression.
    """
    if not self.filter_string:
      return IdentityExpression()

    self.Close()
    return self.Reduce()

  def PopState(self, **unused_kwargs):
    """Pops the previous state from the stack.

    Returns:
      str: parser state.
    """
    try:
      self.state = self.state_stack.pop()
      logging.debug('Returned state to {0:s}'.format(self.state))

      return self.state
    except IndexError:
      self.Error('Tried to pop the state but failed - possible recursion error')

  def PushBack(self, string='', **unused_kwargs):
    """Pushes the match back on the stream.

    Args:
      string (Optional[str]): expression string.
    """
    self.buffer = string + self.buffer
    self.processed_buffer = self.processed_buffer[:-len(string)]

  def PushState(self, **unused_kwargs):
    """Pushes the current state on the state stack."""
    logging.debug('Storing state {0:s}'.format(repr(self.state)))
    self.state_stack.append(self.state)

  def Reduce(self):
    """Reduce the token stack into an AST.

    Returns:
      Expression: expression.
    """
    # Check for sanity
    if self.state != 'INITIAL':
      self.Error('Premature end of expression')

    length = len(self.stack)
    while length > 1:
      # Precedence order
      self._CombineParenthesis()
      self._CombineBinaryExpressions('and')
      self._CombineBinaryExpressions('or')

      # No change
      if len(self.stack) == length:
        break
      length = len(self.stack)

    if length != 1:
      self.Error('Illegal query expression')

    return self.stack[0]

  def StringEscape(self, string, match, **unused_kwargs):
    """Escapes backslashes found inside an expression string.

    Backslashes followed by anything other than ['"rnbt] will just be included
    in the string.

    Args:
      string (str): expression string that matched.
      match (re.MatchObject): match object, where match.group(1) contains
          the escaped code.
    """
    if match.group(1) in '\'"rnbt':
      self.string += string.decode('unicode_escape')
    else:
      self.string += string

  def StringFinish(self, **unused_kwargs):
    """Finishes a string operation.

    Returns:
      str: token or None when the internal state is not "ATTRIBUTE" or
          "ARG_LIST".
    """
    if self.state == 'ATTRIBUTE':
      return self.StoreAttribute(string=self.string)

    if self.state == 'ARG_LIST':
      return self.InsertArg(string=self.string)

    return None

  def StringInsert(self, string='', **unused_kwargs):
    """Adds the expression string to the internal string.

    Args:
      string (Optional[str]): expression string.
    """
    self.string += string

  def StringStart(self, **unused_kwargs):
    """Initializes the internal string."""
    self.string = ''

  def StoreAttribute(self, string='', **unused_kwargs):
    """Store the attribute.

    Args:
      string (Optional[str]): expression string.

    Returns:
      str: token.
    """
    logging.debug('Storing attribute {0:s}'.format(repr(string)))

    # TODO: Update the expected number_of_args
    try:
      self.current_expression.SetAttribute(string)
    except AttributeError:
      raise errors.ParseError('Invalid attribute \'{0:s}\''.format(string))

    return 'OPERATOR'

  def StoreOperator(self, string='', **unused_kwargs):
    """Store the operator.

    Args:
      string (Optional[str]): expression string.
    """
    logging.debug('Storing operator {0:s}'.format(repr(string)))
    self.current_expression.SetOperator(string)
