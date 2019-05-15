# -*- coding: utf-8 -*-
"""A parser for event filter expressions.

The parser is based on the lexer from the GRR project:
https://github.com/google/grr
"""

from __future__ import unicode_literals

import logging
import re

from plaso.lib import errors


class Token(object):
  """An event filter parser token."""

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
    self.state_regex = re.compile(
        state_regex, re.DOTALL | re.M | re.S | re.U | flags)
    self.regex = re.compile(regex, re.DOTALL | re.M | re.S | re.U | flags)
    self.re_str = regex
    self.actions = []
    if actions:
      self.actions = actions.split(',')

    self.next_state = next_state


class Expression(object):
  """An event filter parser expression."""

  attribute = None
  args = None
  operator = None

  # The expected number of args
  number_of_args = 1

  def __init__(self):
    """Initializes an event filter parser expression."""
    super(Expression, self).__init__()
    self.args = []

  def __str__(self):
    """Retrieves a string representation of the expression.

    Returns:
      str: string representation of the expression.
    """
    return 'Expression: ({0:s}) ({1:s}) {2:s}'.format(
        self.attribute, self.operator, self.args)

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

  def Compile(self, unused_filter_implementation):
    """Given a filter implementation, compile this expression."""
    raise NotImplementedError(
        '{0:s} does not implement Compile.'.format(self.__class__.__name__))

  # TODO: rename this function to GetTreeAsString or equivalent.
  def PrintTree(self, depth=''):
    """Print the tree."""
    return '{0:s} {1:s}'.format(depth, self)

  def SetAttribute(self, attribute):
    """Set the attribute."""
    self.attribute = attribute

  def SetOperator(self, operator):
    """Set the operator."""
    self.operator = operator


class BinaryExpression(Expression):
  """An event filter parser expression which takes two other expressions."""

  def __init__(self, operator='', part=None):
    """Initializes an event filter parser binary expression.

    Args:
      operator (str): operator.
      part (str): expression part.
    """
    super(BinaryExpression, self).__init__()
    self.args = []
    self.operator = operator
    if part:
      self.args.append(part)

  def __str__(self):
    """Retrieves a string representation of the binary expression.

    Returns:
      str: string representation of the binary expression.
    """
    return 'Binary Expression: {0:s} {1:s}'.format(
        self.operator, [str(x) for x in self.args])

  def AddOperands(self, lhs, rhs):
    """Adds an operand.

    Args:
      lhs (Expression): left hand side expression.
      rhs (Expression): right hand side expression.

    Raises:
      ParseError: if either left hand side or right hand side expression
          is not an instance of Expression.
    """
    if isinstance(lhs, Expression) and isinstance(rhs, Expression):
      self.args = [lhs, rhs]
    else:
      raise errors.ParseError(
          'Expected expression, got {0:s} {1:s} {2:s}'.format(
              lhs, self.operator, rhs))

  # TODO: rename this function to GetTreeAsString or equivalent.
  def PrintTree(self, depth=''):
    """Prints the binary expression represented as a tree.

    Args:
      depth (Optional[str]): indentation string of the binary expression in
          the tree.

    Returns:
      str: the binary expression represented as a tree.
    """
    result = '{0:s}{1:s}\n'.format(depth, self.operator)
    for part in self.args:
      result += '{0:s}-{1:s}\n'.format(depth, part.PrintTree(depth + '  '))

    return result

  def Compile(self, filter_implementation):
    """Compiles the binary expression into a filter object.

    Args:
      filter_implementation (class): class of the filter object.

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
      filter_implementation (class): class of the filter object.

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
  """
  _CONTINUE_STATE = 'CONTINUE'
  _INITIAL_STATE = 'INITIAL'

  _ERROR_TOKEN = 'Error'

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
    self.current_expression = self.expression_cls()  # Holds expression
    self.error = 0
    self.filter_string = data
    self.flags = 0
    self.processed = 0
    self.processed_buffer = ''
    self.stack = []  # The token stack
    self.state = self._INITIAL_STATE
    self.state_stack = []
    self.string = None
    self.verbose = 0

  def BinaryOperator(self, string=None, **unused_kwargs):
    """Sets the binary operator.

    Args:
      string (Optional[str]): expression string.
    """
    self.stack.append(self.binary_expression_cls(string))

  def BracketOpen(self, **unused_kwargs):
    """Defines an open bracket."""
    self.stack.append('(')

  def BracketClose(self, **unused_kwargs):
    """Defines a closing bracket."""
    self.stack.append(')')

  def Close(self):
    """Forces parse the remaining data in the buffer."""
    while self.NextToken():
      if not self.buffer:
        return

  def Default(self, **kwarg):
    """Default callback handler."""
    logging.debug('Default handler: {0:s}'.format(kwarg))

  def Empty(self):
    """Checks if the buffer is empty.

    Returns:
      bool: True if the buffer is emtpy.
    """
    return not self.buffer

  def Feed(self, data):
    """Feeds the buffer with data.

    Args:
      data (str): data to be processed by the search parser.
    """
    self.buffer = ''.join([self.buffer, data])

  def StringStart(self, **unused_kwargs):
    """Initializes the internal string."""
    self.string = ''

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

  def StringInsert(self, string='', **unused_kwargs):
    """Adds the expression string to the internal string.

    Args:
      string (Optional[str]): expression string.
    """
    self.string += string

  def StringFinish(self, **unused_kwargs):
    """Finishes a string operation.

    Returns:
      str: ??? or None when the internal state is not "ATTRIBUTE" or
          "ARG_LIST".
    """
    if self.state == 'ATTRIBUTE':
      return self.StoreAttribute(string=self.string)

    if self.state == 'ARG_LIST':
      return self.InsertArg(string=self.string)

    return None

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

  def _CombineBinaryExpressions(self, operator):
    """Combines binary expressions.

    Args:
      operator (???): operator.
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

  def Reduce(self):
    """Reduce the token stack into an AST.

    Returns:
      str: token.
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

  def Error(self, message=None, weight=1):  # pylint: disable=unused-argument
    """Raises a parse error.

    Args:
      message (Optional[str]): error message.
      weight (Optional[int]): error weight.

    Raises:
      ParseError: always raised.
    """
    raise errors.ParseError(
        '{0:s} in position {1:s}: {2:s} <----> {3:s} )'.format(
            message, len(self.processed_buffer), self.processed_buffer,
            self.buffer))

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
      str: token.
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
