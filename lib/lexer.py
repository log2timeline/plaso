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
    self.buffer += data

  def Empty(self):
    return not self.buffer

  def Default(self, **kwarg):
    logging.debug("Default handler: %s", kwarg)

  def Error(self, message=None, weight=1):
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
    self.fd = fd
    super(SelfFeederMixIn, self).__init__()

  def NextToken(self):
    # If we dont have enough data - feed ourselves: We assume
    # that we must have at least one sector in our buffer.
    if len(self.buffer) < 512:
      if self.Feed() == 0 and not self.buffer:
        return None

    return Lexer.NextToken(self)

  def Feed(self, size=512):
    data = self.fd.read(size)
    Lexer.Feed(self, data)

    return len(data)
