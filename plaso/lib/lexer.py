#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""An LL(1) lexer. This lexer is very tolerant of errors and can resync.

This lexer is originally copied from the GRR project:
https://code.google.com/p/grr
"""

import logging
import re


class Token(object):
  """A token action."""

  def __init__(self, state_regex, regex, actions, next_state, flags=re.I):
    """Initializes the token object.

    Args:

      state_regex: If this regular expression matches the current state this
                   rule is considered.
      regex: A regular expression to try and match from the current point.
      actions: A command separated list of method names in the Lexer to call.
      next_state: The next state we transition to if this Token matches.
      flags: re flags.
    """
    self.state_regex = re.compile(
        state_regex, re.DOTALL | re.M | re.S | re.U | flags)
    self.regex = re.compile(regex, re.DOTALL | re.M | re.S | re.U | flags)
    self.re_str = regex
    self.actions = []
    if actions:
      self.actions = actions.split(',')

    self.next_state = next_state

  def Action(self, lexer):
    """Method is called when the token matches."""


class Error(Exception):
  """Module exception."""


class ParseError(Error):
  """A parse error occured."""


class Lexer(object):
  """A generic feed lexer."""
  _CONTINUE_STATE = 'CONTINUE'
  _INITIAL_STATE = 'INITIAL'

  _ERROR_TOKEN = 'Error'

  # A list of Token() instances.
  tokens = []

  def __init__(self, data=''):
    """Initializes the lexer object."""
    super(Lexer, self).__init__()
    self.buffer = data
    self.error = 0
    self.flags = 0
    self.processed = 0
    self.processed_buffer = ''
    self.state = self._INITIAL_STATE
    self.state_stack = []
    self.verbose = 0

  def NextToken(self):
    """Fetch the next token by trying to match any of the regexes in order."""
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
        except ParseError as exception:
          self.Error(exception)

      # Update the next state
      if next_state:
        self.state = next_state

      return token

    # Check that we are making progress - if we are too full, we assume we are
    # stuck.
    self.Error(u'Expected {0:s}'.format(self.state))
    self.processed_buffer += self.buffer[:1]
    self.buffer = self.buffer[1:]
    return self._ERROR_TOKEN

  def Feed(self, data):
    """Feed the buffer with data."""
    self.buffer = ''.join([self.buffer, data])

  def Empty(self):
    """Return a boolean indicating if the buffer is empty."""
    return not self.buffer

  def Default(self, **kwarg):
    """The default callback handler."""
    logging.debug(u'Default handler: {0:s}'.format(kwarg))

  def Error(self, message=None, weight=1):
    """Log an error down."""
    logging.debug(u'Error({0:d}): {1:s}'.format(weight, message))
    # Keep a count of errors
    self.error += weight

  def PushState(self, **_):
    """Push the current state on the state stack."""
    logging.debug(u'Storing state {0:s}'.format(repr(self.state)))
    self.state_stack.append(self.state)

  def PopState(self, **_):
    """Pop the previous state from the stack."""
    try:
      self.state = self.state_stack.pop()
      logging.debug(u'Returned state to {0:s}'.format(self.state))

      return self.state
    except IndexError:
      self.Error(
          u'Tried to pop the state but failed - possible recursion error')

  def PushBack(self, string='', **_):
    """Push the match back on the stream."""
    self.buffer = string + self.buffer
    self.processed_buffer = self.processed_buffer[:-len(string)]

  def Close(self):
    """A convenience function to force us to parse all the data."""
    while self.NextToken():
      if not self.buffer:
        return


class SelfFeederMixIn(Lexer):
  """This mixin is used to make a lexer which feeds itself.

  Note that self.file_object must be the file object we read from.
  """

  # TODO: fix this, file object either needs to be set or not passed here.
  def __init__(self, file_object=None):
    """Initializes the lexer feeder min object.

    Args:
      file_object: Optional file-like object. The default is None.
    """
    super(SelfFeederMixIn, self).__init__()
    self.file_object = file_object

  def NextToken(self):
    """Return the next token."""
    # If we don't have enough data - feed ourselves: We assume
    # that we must have at least one sector in our buffer.
    if len(self.buffer) < 512:
      if self.Feed() == 0 and not self.buffer:
        return None

    return Lexer.NextToken(self)

  def Feed(self, size=512):
    """Feed data into the buffer."""
    data = self.file_object.read(size)
    Lexer.Feed(self, data)
    return len(data)


class Expression(object):
  """A class representing an expression."""
  attribute = None
  args = None
  operator = None

  # The expected number of args
  number_of_args = 1

  def __init__(self):
    """Initializes the expression object."""
    self.args = []

  def SetAttribute(self, attribute):
    """Set the attribute."""
    self.attribute = attribute

  def SetOperator(self, operator):
    """Set the operator."""
    self.operator = operator

  def AddArg(self, arg):
    """Adds a new arg to this expression.

    Args:
       arg: The argument to add (string).

    Returns:
      True if this arg is the last arg, False otherwise.

    Raises:
      ParseError: If there are too many args.
    """
    self.args.append(arg)
    if len(self.args) > self.number_of_args:
      raise ParseError(u'Too many args for this expression.')

    elif len(self.args) == self.number_of_args:
      return True

    return False

  def __str__(self):
    """Return a string representation of the expression."""
    return 'Expression: ({0:s}) ({1:s}) {2:s}'.format(
        self.attribute, self.operator, self.args)

  # TODO: rename this function to GetTreeAsString or equivalent.
  def PrintTree(self, depth=''):
    """Print the tree."""
    return u'{0:s} {1:s}'.format(depth, self)

  def Compile(self, unused_filter_implemention):
    """Given a filter implementation, compile this expression."""
    raise NotImplementedError(
        u'{0:s} does not implement Compile.'.format(self.__class__.__name__))


class BinaryExpression(Expression):
  """An expression which takes two other expressions."""

  def __init__(self, operator='', part=None):
    """Initializes the expression object."""
    self.operator = operator
    self.args = []
    if part:
      self.args.append(part)
    super(BinaryExpression, self).__init__()

  def __str__(self):
    """Return a string representation of the binary expression."""
    return 'Binary Expression: {0:s} {1:s}'.format(
        self.operator, [str(x) for x in self.args])

  def AddOperands(self, lhs, rhs):
    """Add an operant."""
    if isinstance(lhs, Expression) and isinstance(rhs, Expression):
      self.args = [lhs, rhs]
    else:
      raise ParseError(u'Expected expression, got {0:s} {1:s} {2:s}'.format(
          lhs, self.operator, rhs))

  # TODO: rename this function to GetTreeAsString or equivalent.
  def PrintTree(self, depth=''):
    """Print the tree."""
    result = u'{0:s}{1:s}\n'.format(depth, self.operator)
    for part in self.args:
      result += u'{0:s}-{1:s}\n'.format(depth, part.PrintTree(depth + '  '))

    return result

  def Compile(self, filter_implemention):
    """Compile the binary expression into a filter object."""
    operator = self.operator.lower()
    if operator == 'and' or operator == '&&':
      method = 'AndFilter'
    elif operator == 'or' or operator == '||':
      method = 'OrFilter'
    else:
      raise ParseError(u'Invalid binary operator {0:s}'.format(operator))

    args = [x.Compile(filter_implemention) for x in self.args]
    return getattr(filter_implemention, method)(*args)


class IdentityExpression(Expression):
  """An Expression which always evaluates to True."""

  def Compile(self, filter_implemention):
    """Compile the expression."""
    return filter_implemention.IdentityFilter()


class SearchParser(Lexer):
  """This parser can parse the mini query language and build an AST.

  Examples of valid syntax:
    filename contains "foo" and (size > 100k or date before "2011-10")
    date between 2011 and 2010
    files older than 1 year
  """

  expression_cls = Expression
  binary_expression_cls = BinaryExpression

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
      Token('.', r'\s+', None, None),
      ]

  def __init__(self, data):
    """Initializes the search parser object."""
    # Holds expression
    self.current_expression = self.expression_cls()
    self.filter_string = data

    # The token stack
    self.stack = []
    Lexer.__init__(self, data)

  def BinaryOperator(self, string=None, **_):
    """Set the binary operator."""
    self.stack.append(self.binary_expression_cls(string))

  def BracketOpen(self, **_):
    """Define an open bracket."""
    self.stack.append('(')

  def BracketClose(self, **_):
    """Close the bracket."""
    self.stack.append(')')

  def StringStart(self, **_):
    """Initialize the string."""
    self.string = ''

  def StringEscape(self, string, match, **_):
    """Escape backslashes found inside a string quote.

    Backslashes followed by anything other than ['"rnbt] will just be included
    in the string.

    Args:
       string: The string that matched.
       match: The match object (m.group(1) is the escaped code)
    """
    if match.group(1) in '\'"rnbt':
      self.string += string.decode('string_escape')
    else:
      self.string += string

  def StringInsert(self, string='', **_):
    """Add to the string."""
    self.string += string

  def StringFinish(self, **_):
    """Finish the string operation."""
    if self.state == 'ATTRIBUTE':
      return self.StoreAttribute(string=self.string)

    elif self.state == 'ARG_LIST':
      return self.InsertArg(string=self.string)

  def StoreAttribute(self, string='', **_):
    """Store the attribute."""
    logging.debug(u'Storing attribute {0:s}'.format(repr(string)))

    # TODO: Update the expected number_of_args
    try:
      self.current_expression.SetAttribute(string)
    except AttributeError:
      raise ParseError(u'Invalid attribute \'{0:s}\''.format(string))

    return 'OPERATOR'

  def StoreOperator(self, string='', **_):
    """Store the operator."""
    logging.debug(u'Storing operator {0:s}'.format(repr(string)))
    self.current_expression.SetOperator(string)

  def InsertArg(self, string='', **_):
    """Insert an arg to the current expression."""
    logging.debug(u'Storing Argument {0:s}'.format(string))

    # This expression is complete
    if self.current_expression.AddArg(string):
      self.stack.append(self.current_expression)
      self.current_expression = self.expression_cls()
      return self.PopState()

  def _CombineBinaryExpressions(self, operator):
    """Combine binary expressions."""
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

    self.stack = filter(None, self.stack)

  def _CombineParenthesis(self):
    """Combine parenthesis."""
    for i in range(len(self.stack)-2):
      if (self.stack[i] == '(' and self.stack[i+2] == ')' and
          isinstance(self.stack[i+1], Expression)):
        self.stack[i] = None
        self.stack[i+2] = None

    self.stack = filter(None, self.stack)

  def Reduce(self):
    """Reduce the token stack into an AST."""
    # Check for sanity
    if self.state != 'INITIAL':
      self.Error(u'Premature end of expression')

    length = len(self.stack)
    while length > 1:
      # Precendence order
      self._CombineParenthesis()
      self._CombineBinaryExpressions('and')
      self._CombineBinaryExpressions('or')

      # No change
      if len(self.stack) == length:
        break
      length = len(self.stack)

    if length != 1:
      self.Error(u'Illegal query expression')

    return self.stack[0]

  def Error(self, message=None, unused_weight=1):
    """Raise an error message."""
    raise ParseError(u'{0:s} in position {1:s}: {2:s} <----> {3:s} )'.format(
        message, len(self.processed_buffer), self.processed_buffer,
        self.buffer))

  def Parse(self):
    """Parse."""
    if not self.filter_string:
      return IdentityExpression()

    self.Close()
    return self.Reduce()
