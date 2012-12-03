#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
    """Constructor.

    Args:

      state_regex: If this regular expression matches the current state this
                   rule is considered.
      regex: A regular expression to try and match from the current point.
      actions: A command separated list of method names in the Lexer to call.
      next_state: The next state we transition to if this Token matches.
      flags: re flags.
    """
    self.state_regex = re.compile(state_regex, re.DOTALL | re.M | re.S | re.U |
                                  flags)
    self.regex = re.compile(regex, re.DOTALL | re.M | re.S | re.U | flags)
    self.re_str = regex
    self.actions = []
    if actions:
      self.actions = actions.split(",")

    self.next_state = next_state

  def Action(self, lexer):
    """Method is called when the token matches."""


class Error(Exception):
  """Module exception."""


class ParseError(Error):
  """A parse error occured."""


class Lexer(object):
  """A generic feed lexer."""
  # A list of Token() instances.
  tokens = []

  # The first state
  state = "INITIAL"

  # The buffer we are parsing now
  buffer = ""
  error = 0
  verbose = 0

  # The index into the buffer where we are currently pointing
  processed = 0
  processed_buffer = ""

  # Regex flags
  flags = 0

  def __init__(self, data=""):
    """Constructor."""
    self.buffer = data
    self.state_stack = []

  def NextToken(self):
    """Fetch the next token by trying to match any of the regexes in order."""
    current_state = self.state
    for token in self.tokens:
      # Does the rule apply to us?
      if not token.state_regex.match(current_state): continue

      # Try to match the rule
      m = token.regex.match(self.buffer)
      if not m: continue

      # The match consumes the data off the buffer (the handler can put it back
      # if it likes)
      self.processed_buffer += self.buffer[:m.end()]
      self.buffer = self.buffer[m.end():]
      self.processed += m.end()

      next_state = token.next_state
      for action in token.actions:

        # Is there a callback to handle this action?
        cb = getattr(self, action, self.Default)

        # Allow a callback to skip other callbacks.
        try:
          possible_next_state = cb(string=m.group(0), match=m)
          if possible_next_state == "CONTINUE":
            continue
          # Override the state from the Token
          elif possible_next_state:
            next_state = possible_next_state
        except ParseError as e:
          self.Error(e)

      # Update the next state
      if next_state:
        self.state = next_state

      return token

    # Check that we are making progress - if we are too full, we assume we are
    # stuck.
    self.Error("Expected %s" % (self.state))
    self.processed_buffer += self.buffer[:1]
    self.buffer = self.buffer[1:]
    return "Error"

  def Feed(self, data):
    """Feed the buffer with data."""
    self.buffer += data

  def Empty(self):
    """Return a boolean indicating if the buffer is empty."""
    return not self.buffer

  def Default(self, **kwarg):
    """The default callback handler."""
    logging.debug("Default handler: %s", kwarg)

  def Error(self, message=None, weight=1):
    """Log an error down."""
    logging.debug("Error(%s): %s", weight, message)
    # Keep a count of errors
    self.error += weight

  def PushState(self, **_):
    """Push the current state on the state stack."""
    logging.debug("Storing state %r", self.state)
    self.state_stack.append(self.state)

  def PopState(self, **_):
    """Pop the previous state from the stack."""
    try:
      self.state = self.state_stack.pop()
      logging.debug("Returned state to %s", self.state)

      return self.state
    except IndexError:
      self.Error("Tried to pop the state but failed - possible recursion error")

  def PushBack(self, string="", **_):
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

  Note that self.fd must be the fd we read from.
  """

  def __init__(self, fd=""):
    """Constructor."""
    self.fd = fd
    super(SelfFeederMixIn, self).__init__()

  def NextToken(self):
    """Return the next token."""
    # If we dont have enough data - feed ourselves: We assume
    # that we must have at least one sector in our buffer.
    if len(self.buffer) < 512:
      if self.Feed() == 0 and not self.buffer:
        return None

    return Lexer.NextToken(self)

  def Feed(self, size=512):
    """Feed data into the buffer."""
    data = self.fd.read(size)
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
    """Constructor."""
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
      raise ParseError("Too many args for this expression.")

    elif len(self.args) == self.number_of_args:
      return True

    return False

  def __str__(self):
    """Return a string representation of the expression."""
    return "Expression: (%s) (%s) %s" % (
        self.attribute, self.operator, self.args)

  def PrintTree(self, depth=""):
    """Print the tree."""
    return "%s %s" % (depth, self)

  def Compile(self, unused_filter_implemention):
    """Given a filter implementation, compile this expression."""
    raise NotImplementedError("%s does not implement Compile." %
                              self.__class__.__name__)


class BinaryExpression(Expression):
  """An expression which takes two other expressions."""

  def __init__(self, operator="", part=None):
    """Constructor for the binary expression."""
    self.operator = operator
    self.args = []
    if part: self.args.append(part)
    super(BinaryExpression, self).__init__()

  def __str__(self):
    """Return a string representation of the binary expression."""
    return "Binary Expression: %s %s" % (
        self.operator, [str(x) for x in self.args])

  def AddOperands(self, lhs, rhs):
    """Add an operant."""
    if isinstance(lhs, Expression) and isinstance(rhs, Expression):
      self.args = [lhs, rhs]
    else:
      raise ParseError("Expected expression, got %s %s %s" % (
          lhs, self.operator, rhs))

  def PrintTree(self, depth=""):
    """Print the tree."""
    result = "%s%s\n" % (depth, self.operator)
    for part in self.args:
      result += "%s-%s\n" % (depth, part.PrintTree(depth + "  "))

    return result

  def Compile(self, filter_implemention):
    """Compile the binary expression into a filter object."""
    operator = self.operator.lower()
    if operator == "and" or operator == "&&":
      method = "AndFilter"
    elif operator == "or" or operator == "||":
      method = "OrFilter"
    else:
      raise ParseError("Invalid binary operator %s" % operator)

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
      Token("STRING", "\"", "PopState,StringFinish", None),
      Token("STRING", r"\\(.)", "StringEscape", None),
      Token("STRING", r"[^\\\"]+", "StringInsert", None),

      # Single quoted string
      Token("SQ_STRING", "'", "PopState,StringFinish", None),
      Token("SQ_STRING", r"\\(.)", "StringEscape", None),
      Token("SQ_STRING", r"[^\\']+", "StringInsert", None),

      # TODO(user): Implement a unary not operator.
      # The first thing we see in the initial state takes up to the ATTRIBUTE
      Token("INITIAL", "(and|or|\&\&|\|\|)", "BinaryOperator", None),
      Token("INITIAL", r"[^\s\(\)]", "PushState,PushBack", "ATTRIBUTE"),
      Token("INITIAL", "\(", "BracketOpen", None),
      Token("INITIAL", r"\)", "BracketClose", None),

      Token("ATTRIBUTE", "[\w._0-9]+", "StoreAttribute", "OPERATOR"),
      Token("OPERATOR", "[a-z0-9<>=\-\+\!\^\&%]+", "StoreOperator", "ARG_LIST"),
      Token("OPERATOR", "(!=|[<>=])", "StoreSpecialOperator", "ARG_LIST"),
      Token("ARG_LIST", "[^\s'\"]+", "InsertArg", None),

      # Start a string.
      Token(".", "\"", "PushState,StringStart", "STRING"),
      Token(".", "'", "PushState,StringStart", "SQ_STRING"),

      # Skip whitespace.
      Token(".", r"\s+", None, None),
      ]

  def __init__(self, data):
    """Constructor for the search parser."""
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
    self.stack.append("(")

  def BracketClose(self, **_):
    """Close the bracket."""
    self.stack.append(")")

  def StringStart(self, **_):
    """Initialize the string."""
    self.string = ""

  def StringEscape(self, string, match, **_):
    """Escape backslashes found inside a string quote.

    Backslashes followed by anything other than ['"rnbt] will just be included
    in the string.

    Args:
       string: The string that matched.
       match: The match object (m.group(1) is the escaped code)
    """
    if match.group(1) in "'\"rnbt":
      self.string += string.decode("string_escape")
    else:
      self.string += string

  def StringInsert(self, string="", **_):
    """Add to the string."""
    self.string += string

  def StringFinish(self, **_):
    """Finish the string operation."""
    if self.state == "ATTRIBUTE":
      return self.StoreAttribute(string=self.string)

    elif self.state == "ARG_LIST":
      return self.InsertArg(string=self.string)

  def StoreAttribute(self, string="", **_):
    """Store the attribute."""
    logging.debug("Storing attribute %r", string)

    # TODO(user): Update the expected number_of_args
    try:
      self.current_expression.SetAttribute(string)
    except AttributeError:
      raise ParseError("Invalid attribute '%s'" % string)

    return "OPERATOR"

  def StoreOperator(self, string="", **_):
    """Store the operator."""
    logging.debug("Storing operator %r", string)
    self.current_expression.SetOperator(string)

  def InsertArg(self, string="", **_):
    """Insert an arg to the current expression."""
    logging.debug("Storing Argument %s", string)

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
      if (self.stack[i] == "(" and self.stack[i+2] == ")" and
          isinstance(self.stack[i+1], Expression)):
        self.stack[i] = None
        self.stack[i+2] = None

    self.stack = filter(None, self.stack)

  def Reduce(self):
    """Reduce the token stack into an AST."""
    # Check for sanity
    if self.state != "INITIAL":
      self.Error("Premature end of expression")

    length = len(self.stack)
    while length > 1:
      # Precendence order
      self._CombineParenthesis()
      self._CombineBinaryExpressions("and")
      self._CombineBinaryExpressions("or")

      # No change
      if len(self.stack) == length: break
      length = len(self.stack)

    if length != 1:
      self.Error("Illegal query expression")

    return self.stack[0]

  def Error(self, message=None, unused_weight=1):
    """Raise an error message."""
    raise ParseError("%s in position %s: %s <----> %s )" % (
        message, len(self.processed_buffer), self.processed_buffer,
        self.buffer))

  def Parse(self):
    """Parse."""
    if not self.filter_string:
      return IdentityExpression()

    self.Close()
    return self.Reduce()
