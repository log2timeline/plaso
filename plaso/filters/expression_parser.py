# -*- coding: utf-8 -*-
"""Classes to perform filtering of objects based on their data members.

Given a list of objects and a textual filter expression, these classes allow
you to determine which objects match the filter. The system has two main
pieces: A parser for the supported grammar and a filter implementation.

Given any complying user-supplied grammar, it is parsed with a custom lexer
based on GRR's lexer and then compiled into an actual implementation by using
the filter implementation. A filter implementation simply provides actual
implementations for the primitives required to perform filtering. The compiled
result is always a class supporting the Filter interface.

If we define a class called Car such as:


class Car(object):
  def __init__(self, code, color="white", doors=3):
    self.code = code
    self.color = color
    self.doors = 3

And we have two instances:

  ford_ka = Car("FORDKA1", color="grey")
  toyota_corolla = Car("COROLLA1", color="white", doors=5)
  fleet = [ford_ka, toyota_corolla]

We want to find cars that are grey and have 3 or more doors. We could filter
our fleet like this:

  criteria = "(color is grey) and (doors >= 3)"
  parser = ContextFilterParser(criteria).Parse()
  compiled_filter = parser.Compile(LowercaseAttributeFilterImp)

  for car in fleet:
    if compiled_filter.Matches(car):
      print("Car %s matches the supplied filter." % car.code)

The filter expression contains two subexpressions joined by an AND operator:
  "color is grey" and "doors >= 3"

This means we want to search for objects matching these two subexpressions.
Let's analyze the first one in depth "color is grey":

  "color": the left operand specifies a search path to look for the data. This
  tells our filtering system to look for the color property on passed objects.
  "is": the operator. Values retrieved for the "color" property will be checked
  against the right operand to see if they are equal.
  "grey": the right operand. It specifies an explicit value to check for.

So each time an object is passed through the filter, it will expand the value
of the color data member, and compare its value against "grey".

Because data members of objects are often not simple datatypes but other
objects, the system allows you to reference data members within other data
members by separating each by a dot. Let's see an example:

Let's add a more complex Car class with default tyre data:


class CarWithTyres(Car):
  def __init__(self, code, tyres=None, color="white", doors=3):
    super(self, CarWithTyres).__init__(code, color, doors)
    tyres = tyres or Tyre("Pirelli", "PZERO")


class Tyre(object):
  def __init__(self, brand, code):
    self.brand = brand
    self.code = code

And two new instances:
  ford_ka = CarWithTyres("FORDKA", color="grey", tyres=Tyre("AVON", "ZT5"))
  toyota_corolla = Car("COROLLA1", color="white", doors=5)
  fleet = [ford_ka, toyota_corolla]

To filter a car based on the tyre brand, we would use a search path of
"tyres.brand".

Because the filter implementation provides the actual classes that perform
handling of the search paths, operators, etc. customizing the behavior of the
filter is easy. Three basic filter implementations are given:

  BaseFilterImplementation: search path expansion is done on attribute names
  as provided (case-sensitive).
  LowercaseAttributeFilterImp: search path expansion is done on the lowercased
  attribute name, so that it only accesses attributes, not methods.
  DictFilterImplementation: search path expansion is done on dictionary access
  to the given object. So "a.b" expands the object obj to obj["a"]["b"]
"""

from __future__ import unicode_literals

import binascii
import codecs
import logging
import re

from plaso.filters import expressions
from plaso.filters import filters
from plaso.filters import value_expanders
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


class EventFilterExpressionParser(object):
  """Event filter expression parser.

  Examples of valid syntax:
    size is 40
    (name contains "Program Files" AND hash.md5 is "123abc")
    @imported_modules (num_symbols = 14 AND symbol.name is "FindWindow")

  Attributes:
    buffer (str): buffer that holds the expression.
    current_expression (Expression): current expression.
    error (int): ???
    filter_string (str): ???
    flags (int): ???
    flipped (bool): ???
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
  expression_cls = expressions.EventExpression
  binary_expression_cls = expressions.BinaryExpression

  tokens = [
      # Operators and related tokens
      Token('INITIAL', r'\@[\w._0-9]+', 'ContextOperator,PushState',
            'CONTEXTOPEN'),
      Token('INITIAL', r'[^\s\(\)]', 'PushState,PushBack', 'ATTRIBUTE'),
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
      Token('OPERATOR', r'not ', 'FlipLogic', None),
      Token('OPERATOR', r'(\w+|[<>!=]=?)', 'StoreOperator', 'CHECKNOT'),
      Token('CHECKNOT', r'not', 'FlipLogic', 'ARG'),
      Token('CHECKNOT', r'\s+', None, None),
      Token('CHECKNOT', r'([^not])', 'PushBack', 'ARG'),
      Token('ARG', r'(\d+\.\d+)', 'InsertFloatArg', 'ARG'),
      Token('ARG', r'(0x\d+)', 'InsertInt16Arg', 'ARG'),
      Token('ARG', r'(\d+)', 'InsertIntArg', 'ARG'),
      Token('ARG', '"', 'PushState,StringStart', 'STRING'),
      Token('ARG', '\'', 'PushState,StringStart', 'SQ_STRING'),
      # When the last parameter from arg_list has been pushed

      # State where binary operators are supported (AND, OR)
      Token('BINARY', r'(?i)(and|or|\&\&|\|\|)', 'BinaryOperator', 'INITIAL'),
      # - We can also skip spaces
      Token('BINARY', r'\s+', None, None),
      # - But if it's not "and" or just spaces we have to go back
      Token('BINARY', '.', 'PushBack,PopState', None),

      # Skip whitespace.
      Token('.', r'\s+', None, None)]

  def __init__(self, data=''):
    """Initializes an event filter expression parser.

    Args:
      data (str): initial data to be processed by the parser.
    """
    super(EventFilterExpressionParser, self).__init__()
    self.buffer = data
    self.current_expression = self.expression_cls()
    self.error = 0
    self.filter_string = data
    self.flags = 0
    self.flipped = None
    self.processed = 0
    self.processed_buffer = ''
    self.stack = []
    self.state = self._INITIAL_STATE
    self.state_stack = []
    self.string = None

  def _CombineContext(self):
    """Combines a context expression."""
    # Context can merge from item 0
    for i in range(len(self.stack)-1, 0, -1):
      item = self.stack[i-1]
      if (isinstance(item, expressions.ContextExpression) and
          isinstance(self.stack[i], expressions.Expression)):
        expression = self.stack[i]
        self.stack[i-1].SetExpression(expression)
        self.stack[i] = None

    self.stack = list(filter(None, self.stack))

  def _CombineBinaryExpressions(self, operator):
    """Combines a binary expression.

    Args:
      operator (str): operator, such as "and" or "&&".
    """
    for i in range(1, len(self.stack)-1):
      item = self.stack[i]
      if (isinstance(item, expressions.BinaryExpression) and
          item.operator.lower() == operator.lower() and
          isinstance(self.stack[i-1], expressions.Expression) and
          isinstance(self.stack[i+1], expressions.Expression)):
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
          isinstance(self.stack[i+1], expressions.Expression)):
        self.stack[i] = None
        self.stack[i+2] = None

    self.stack = list(filter(None, self.stack))

  def BinaryOperator(self, string=None, **unused_kwargs):
    """Sets a binary operator.

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

  def ContextOperator(self, string='', **unused_kwargs):
    """Sets a context operator.

    Args:
      string (str): operator.
    """
    context_expression = expressions.ContextExpression(attribute=string[1:])
    self.stack.append(context_expression)

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
    # Note that none of the values necessarily are strings.
    raise errors.ParseError(
        '{0!s} in position {1!s}: {2!s} <----> {3!s} )'.format(
            message, len(self.processed_buffer), self.processed_buffer,
            self.buffer))

  def Feed(self, data):
    """Feeds the buffer with data.

    Args:
      data (str): data to be processed by the parser.
    """
    self.buffer = ''.join([self.buffer, data])

  def FlipAllowed(self):
    """Raise an error if the not keyword is used where it is not allowed."""
    if not hasattr(self, 'flipped'):
      raise errors.ParseError('Not defined.')

    if not self.flipped:
      return

    if self.current_expression.operator:
      if not self.current_expression.operator.lower() in (
          'is', 'contains', 'inset', 'equals'):
        raise errors.ParseError(
            'Keyword \'not\' does not work against operator: {0:s}'.format(
                self.current_expression.operator))

  def FlipLogic(self, **unused_kwargs):
    """Flip the boolean logic of the expression.

    If an expression is configured to return True when the condition
    is met this logic will flip that to False, and vice versa.
    """
    if hasattr(self, 'flipped') and self.flipped:
      raise errors.ParseError(
          'The operator \'not\' can only be expressed once.')

    if self.current_expression.args:
      raise errors.ParseError(
          'Unable to place the keyword \'not\' after an argument.')

    self.flipped = True

    # Check if this flip operation should be allowed.
    self.FlipAllowed()

    if hasattr(self.current_expression, 'FlipBool'):
      self.current_expression.FlipBool()
      logging.debug('Negative matching [flipping boolean logic].')
    else:
      logging.warning(
          'Unable to perform a negative match, issuing a positive one.')

  def HexEscape(self, string, match, **unused_kwargs):
    """Converts a hex escaped string."""
    logging.debug('HexEscape matched {0:s}.'.format(string))
    hex_string = match.group(1)
    try:
      hex_string = binascii.unhexlify(hex_string)
      hex_string = codecs.decode(hex_string, 'utf-8')
      self.string += hex_string
    except (TypeError, binascii.Error):
      raise errors.ParseError('Invalid hex escape {0!s}.'.format(hex_string))

  def InsertArg(self, string='', **unused_kwargs):
    """Inserts an argument into the current expression.

    Args:
      string (Optional[str]): argument string.

    Returns:
      str: state or None if the argument could not be added to the current
          expression.
    """
    # Note that "string" is not necessarily of type string.
    logging.debug('Storing argument: {0!s}'.format(string))

    # Check if this flip operation should be allowed.
    self.FlipAllowed()

    # This expression is complete
    if self.current_expression.AddArg(string):
      self.stack.append(self.current_expression)
      self.current_expression = self.expression_cls()
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
    """
    try:
      float_value = float(string)
    except (TypeError, ValueError):
      raise errors.ParseError('{0:s} is not a valid float.'.format(string))
    return self.InsertArg(float_value)

  def InsertIntArg(self, string='', **unused_kwargs):
    """Inserts a decimal integer argument into the current expression.

    Args:
      string (Optional[str]): argument string that contains an integer value
          formatted in decimal.

    Returns:
      str: state or None if the argument could not be added to the current
          expression.
    """
    try:
      int_value = int(string)
    except (TypeError, ValueError):
      raise errors.ParseError('{0:s} is not a valid integer.'.format(string))
    return self.InsertArg(int_value)

  def InsertInt16Arg(self, string='', **unused_kwargs):
    """Inserts a hexadecimal integer argument into the current expression.

    Args:
      string (Optional[str]): argument string that contains an integer value
          formatted in hexadecimal.

    Returns:
      str: state or None if the argument could not be added to the current
          expression.
    """
    try:
      int_value = int(string, 16)
    except (TypeError, ValueError):
      raise errors.ParseError(
          '{0:s} is not a valid base16 integer.'.format(string))
    return self.InsertArg(int_value)

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
      return expressions.IdentityExpression()

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
    """Reduce the token stack into an abstract syntax tree (AST).

    Returns:
      Expression: first expression in the AST.
    """
    # Check for sanity
    if self.state != 'INITIAL' and self.state != 'BINARY':
      self.Error('Premature end of expression')

    length = len(self.stack)
    while length > 1:
      # Precedence order
      self._CombineParenthesis()
      self._CombineBinaryExpressions('and')
      self._CombineBinaryExpressions('or')
      self._CombineContext()

      # No change
      if len(self.stack) == length:
        break
      length = len(self.stack)

    if length != 1:
      self.Error('Illegal query expression')

    return self.stack[0]

  def StringEscape(self, string, match, **unused_kwargs):
    """Escapes backslashes found inside an expression string.

    Backslashes followed by anything other than [\'"rnbt.ws] will raise
    an Error.

    Args:
      string (str): string that matched.
      match (re.MatchObject): the match object, where match.group(1) contains
          the escaped code.

    Raises:
      ParseError: When the escaped string is not one of [\'"rnbt].
    """
    if match.group(1) not in '\\\'"rnbt\\.ws':
      raise errors.ParseError('Invalid escape character {0:s}.'.format(string))

    self.string += codecs.decode(string, 'unicode_escape')

  def StringFinish(self, **unused_kwargs):
    """Finishes a string operation.

    Returns:
      str: token or None when the internal state is not "ATTRIBUTE" or
          "ARG".
    """
    if self.state == 'ATTRIBUTE':
      return self.StoreAttribute(string=self.string)

    if self.state == 'ARG':
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

    self.flipped = False

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


class BaseFilterImplementation(object):
  """Defines the base implementation of an object filter by its attributes.

  Inherit from this class, switch any of the needed operators and pass it to
  the Compile method of a parsed string to obtain an executable filter.
  """

  OPS = {
      '==': filters.Equals,
      '>': filters.Greater,
      '>=': filters.GreaterEqual,
      '<': filters.Less,
      '<=': filters.LessEqual,
      '!=': filters.NotEquals,
      'contains': filters.Contains,
      'equals': filters.Equals,
      'inset': filters.InSet,
      'iregexp': filters.RegexpInsensitive,
      'is': filters.Equals,
      'regexp': filters.Regexp}

  FILTERS = {
      'AndFilter': filters.AndFilter,
      'Context': filters.Context,
      'IdentityFilter': filters.IdentityFilter,
      'OrFilter': filters.OrFilter,
      'ValueExpander': value_expanders.PlasoValueExpander}
