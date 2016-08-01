#!/usr/bin/env python
#
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
handling of the search paths, operators, etc. customizing the behaviour of the
filter is easy. Three basic filter implementations are given:

  BaseFilterImplementation: search path expansion is done on attribute names
  as provided (case-sensitive).
  LowercaseAttributeFilterImp: search path expansion is done on the lowercased
  attribute name, so that it only accesses attributes, not methods.
  DictFilterImplementation: search path expansion is done on dictionary access
  to the given object. So "a.b" expands the object obj to obj["a"]["b"]
"""

import abc
import binascii
import logging
import re

from plaso.lib import errors
from plaso.lib import lexer
from plaso.lib import py2to3


# pylint: disable=attribute-defined-outside-init
# pylint: disable=missing-docstring

def GetUnicodeString(string):
  """Converts the string to Unicode if necessary."""
  if not isinstance(string, py2to3.UNICODE_TYPE):
    return str(string).decode(u'utf8', errors=u'ignore')
  return string


class InvalidNumberOfOperands(errors.Error):
  """The number of operands provided to this operator is wrong."""


class Filter(object):
  """Base class for every filter."""

  def __init__(self, arguments=None, value_expander=None):
    """Constructor.

    Args:
      arguments: Arguments to the filter.
      value_expander: A callable that will be used to expand values for the
      objects passed to this filter. Implementations expanders are provided by
      subclassing ValueExpander.

    Raises:
      ValueError: If the given value_expander is not a subclass of ValueExpander
    """
    self.value_expander = None
    self.value_expander_cls = value_expander
    if self.value_expander_cls:
      if not issubclass(self.value_expander_cls, ValueExpander):
        raise ValueError(u'{0:s} is not a valid value expander'.format(
            self.value_expander_cls))
      self.value_expander = self.value_expander_cls()
    self.args = arguments or []
    logging.debug(u'Adding {0:s}'.format(arguments))

  @abc.abstractmethod
  def Matches(self, obj):
    """Whether object obj matches this filter."""

  def Filter(self, objects):
    """Returns a list of objects that pass the filter."""
    return filter(self.Matches, objects)

  def __str__(self):
    return '{0:s}({1:s})'.format(
        self.__class__.__name__, ', '.join([str(arg) for arg in self.args]))


class AndFilter(Filter):
  """Performs a boolean AND of the given Filter instances as arguments.

    Note that if no conditions are passed, all objects will pass.
  """
  def Matches(self, obj):
    for child_filter in self.args:
      if not child_filter.Matches(obj):
        return False
    return True


class OrFilter(Filter):
  """Performs a boolean OR of the given Filter instances as arguments.

  Note that if no conditions are passed, all objects will pass.
  """
  def Matches(self, obj):
    if not self.args:
      return True

    for child_filter in self.args:
      if child_filter.Matches(obj):
        return True
    return False


# pylint: disable=abstract-method
class Operator(Filter):
  """Base class for all operators."""


class IdentityFilter(Operator):
  def Matches(self, _):
    return True


class UnaryOperator(Operator):
  """Base class for unary operators."""

  def __init__(self, operand, **kwargs):
    """Constructor."""
    super(UnaryOperator, self).__init__(arguments=[operand], **kwargs)
    if len(self.args) != 1:
      raise InvalidNumberOfOperands(
          u'Only one operand is accepted by {0:s}. Received {1:d}.'.format(
              self.__class__.__name__, len(self.args)))


class BinaryOperator(Operator):
  """Base class for binary operators.

  The left operand is always a path into the object which will be expanded for
  values. The right operand is a value defined at initialization and is stored
  at self.right_operand.
  """
  def __init__(self, arguments=None, **kwargs):
    super(BinaryOperator, self).__init__(arguments=arguments, **kwargs)
    if len(self.args) != 2:
      raise InvalidNumberOfOperands(
          u'Only two operands are accepted by {0:s}. Received {1:s}.'.format(
              self.__class__.__name__, len(self.args)))

    self.left_operand = self.args[0]
    self.right_operand = self.args[1]


class GenericBinaryOperator(BinaryOperator):
  """Allows easy implementations of operators."""

  def __init__(self, **kwargs):
    super(GenericBinaryOperator, self).__init__(**kwargs)
    self.bool_value = True

  def FlipBool(self):
    logging.debug(u'Negative matching.')
    self.bool_value = not self.bool_value

  def Operation(self, x, y):
    """Performs the operation between two values."""

  def Operate(self, values):
    """Takes a list of values and if at least one matches, returns True."""
    for val in values:
      try:
        if self.Operation(val, self.right_operand):
          return True
        else:
          continue
      except (ValueError, TypeError):
        continue
    return False

  def Matches(self, obj):
    key = self.left_operand
    values = self.value_expander.Expand(obj, key)
    if values and self.Operate(values):
      return self.bool_value
    return not self.bool_value


class Equals(GenericBinaryOperator):
  """Matches objects when the right operand equals the expanded value."""

  def Operation(self, x, y):
    return x == y


class NotEquals(Equals):
  """Matches when the right operand isn't equal to the expanded value."""

  def __init__(self, **kwargs):
    super(NotEquals, self).__init__(**kwargs)
    self.bool_value = False


class Less(GenericBinaryOperator):
  """Whether the expanded value >= right_operand."""

  def Operation(self, x, y):
    return x < y


class LessEqual(GenericBinaryOperator):
  """Whether the expanded value <= right_operand."""

  def Operation(self, x, y):
    return x <= y


class Greater(GenericBinaryOperator):
  """Whether the expanded value > right_operand."""

  def Operation(self, x, y):
    return x > y


class GreaterEqual(GenericBinaryOperator):
  """Whether the expanded value >= right_operand."""

  def Operation(self, x, y):
    return x >= y


class Contains(GenericBinaryOperator):
  """Whether the right operand is contained in the value."""

  def Operation(self, x, y):
    if isinstance(x, py2to3.STRING_TYPES):
      return y.lower() in x.lower()

    return y in x


class InSet(GenericBinaryOperator):
  # TODO(user): Change to an N-ary Operator?
  """Whether all values are contained within the right operand."""

  def Operation(self, x, y):
    """Whether x is fully contained in y."""
    if x in y:
      return True

    # x might be an iterable
    # first we need to skip strings or we'll do silly things
    if (isinstance(x, py2to3.STRING_TYPES)
        or isinstance(x, bytes)):
      return False

    try:
      for value in x:
        if value not in y:
          return False
      return True
    except TypeError:
      return False


class Regexp(GenericBinaryOperator):
  """Whether the value matches the regexp in the right operand."""

  def __init__(self, *children, **kwargs):
    super(Regexp, self).__init__(*children, **kwargs)
    # Note that right_operand is not necessarily a string.
    logging.debug(u'Compiled: {0!s}'.format(self.right_operand))
    try:
      self.compiled_re = re.compile(
          GetUnicodeString(self.right_operand), re.DOTALL)
    except re.error:
      raise ValueError(u'Regular expression "{0!s}" is malformed.'.format(
          self.right_operand))

  def Operation(self, x, unused_y):
    try:
      if self.compiled_re.search(GetUnicodeString(x)):
        return True
    except TypeError:
      pass

    return False


class RegexpInsensitive(Regexp):
  """Whether the value matches the regexp in the right operand."""

  def __init__(self, *children, **kwargs):
    super(RegexpInsensitive, self).__init__(*children, **kwargs)
    # Note that right_operand is not necessarily a string.
    logging.debug(u'Compiled: {0!s}'.format(self.right_operand))
    try:
      self.compiled_re = re.compile(GetUnicodeString(self.right_operand),
                                    re.I | re.DOTALL)
    except re.error:
      raise ValueError(u'Regular expression "{0!s}" is malformed.'.format(
          self.right_operand))


class Context(Operator):
  """Restricts the child operators to a specific context within the object.

  Solves the context problem. The context problem is the following:
  Suppose you store a list of loaded DLLs within a process. Suppose that for
  each of these DLLs you store the number of imported functions and each of the
  imported functions name.

  Imagine that a malicious DLL is injected into processes and its indicators are
  that it only imports one function and that it is RegQueryValueEx. You'd write
  your indicator like this:


  AndOperator(
    Equal("ImportedDLLs.ImpFunctions.Name", "RegQueryValueEx"),
    Equal("ImportedDLLs.NumImpFunctions", "1")
    )

  Now imagine you have these two processes on a given system.

  Process1
  * __ImportedDlls

    * __Name: "notevil.dll"

      * __ImpFunctions

        * __Name: "CreateFileA"

      * __NumImpFunctions: 1

    * __Name: "alsonotevil.dll"

      * __ImpFunctions

        * __Name: "RegQueryValueEx"
        * __Name: "CreateFileA"

      * __NumImpFunctions: 2

  Process2
  * __ImportedDlls

    * __Name: "evil.dll"

      * __ImpFunctions

        * __Name: "RegQueryValueEx"

      * __NumImpFunctions: 1

  Both Process1 and Process2 match your query, as each of the indicators are
  evaluated separately. While you wanted to express "find me processes that
  have a DLL that has both one imported function and ReqQueryValueEx is in the
  list of imported functions", your indicator actually means "find processes
  that have at least a DLL with 1 imported functions and at least one DLL that
  imports the ReqQueryValueEx function".

  To write such an indicator you need to specify a context of ImportedDLLs for
  these two clauses. Such that you convert your indicator to::

      Context("ImportedDLLs",
              AndOperator(
                Equal("ImpFunctions.Name", "RegQueryValueEx"),
                Equal("NumImpFunctions", "1")
              ))

  Context will execute the filter specified as the second parameter for each of
  the objects under "ImportedDLLs", thus applying the condition per DLL, not per
  object and returning the right result.
  """

  def __init__(self, arguments=None, **kwargs):
    if len(arguments) != 2:
      raise InvalidNumberOfOperands(u'Context accepts only 2 operands.')
    super(Context, self).__init__(arguments=arguments, **kwargs)
    self.context, self.condition = self.args

  def Matches(self, obj):
    for object_list in self.value_expander.Expand(obj, self.context):
      for sub_object in object_list:
        if self.condition.Matches(sub_object):
          return True
    return False


OP2FN = {
    'equals': Equals,
    'is': Equals,
    '==': Equals,
    '!=': NotEquals,
    'contains': Contains,
    '>': Greater,
    '>=': GreaterEqual,
    '<': Less,
    '<=': LessEqual,
    'inset': InSet,
    'regexp': Regexp,
    'iregexp': RegexpInsensitive}


class ValueExpander(object):
  """Encapsulates the logic to expand values available in an object.

  Once instantiated and called, this class returns all the values that follow a
  given field path.
  """

  FIELD_SEPARATOR = '.'

  def _GetAttributeName(self, path):
    """Returns the attribute name to fetch given a path."""
    return path[0]

  def _GetValue(self, unused_obj, unused_attr_name):
    """Returns the value of tha attribute attr_name."""
    raise NotImplementedError()

  def _AtLeaf(self, attr_value):
    """Called when at a leaf value. Should yield a value."""
    yield attr_value

  def _AtNonLeaf(self, attr_value, path):
    """Called when at a non-leaf value. Should recurse and yield values."""
    try:
      # Check first for iterables
      # If it's a dictionary, we yield it
      if isinstance(attr_value, dict):
        yield attr_value
      else:
        # If it's an iterable, we recurse on each value.
        for sub_obj in attr_value:
          for value in self.Expand(sub_obj, path[1:]):
            yield value
    except TypeError:  # This is then not iterable, we recurse with the value
      for value in self.Expand(attr_value, path[1:]):
        yield value

  def Expand(self, obj, path):
    """Returns a list of all the values for the given path in the object obj.

    Given a path such as ["sub1", "sub2"] it returns all the values available
    in obj.sub1.sub2 as a list. sub1 and sub2 must be data attributes or
    properties.

    If sub1 returns a list of objects, or a generator, Expand aggregates the
    values for the remaining path for each of the objects, thus returning a
    list of all the values under the given path for the input object.

    Args:
      obj: An object that will be traversed for the given path
      path: A list of strings

    Yields:
      The values once the object is traversed.
    """
    if isinstance(path, py2to3.STRING_TYPES):
      path = path.split(self.FIELD_SEPARATOR)

    attr_name = self._GetAttributeName(path)
    attr_value = self._GetValue(obj, attr_name)
    if attr_value is None:
      return

    if len(path) == 1:
      for value in self._AtLeaf(attr_value):
        yield value
    else:
      for value in self._AtNonLeaf(attr_value, path):
        yield value


class AttributeValueExpander(ValueExpander):
  """An expander that gives values based on object attribute names."""

  def _GetValue(self, obj, attr_name):
    return getattr(obj, attr_name, None)


class LowercaseAttributeValueExpander(AttributeValueExpander):
  """An expander that lowercases all attribute names before access."""

  def _GetAttributeName(self, path):
    return path[0].lower()


class DictValueExpander(ValueExpander):
  """An expander that gets values from dictionary access to the object."""

  def _GetValue(self, obj, attr_name):
    return obj.get(attr_name, None)


class BasicExpression(lexer.Expression):
  """Basic Expression."""

  def __init__(self):
    super(BasicExpression, self).__init__()
    self.bool_value = True

  def FlipBool(self):
    self.bool_value = not self.bool_value

  def Compile(self, filter_implementation):
    arguments = [self.attribute]
    op_str = self.operator.lower()
    operator = filter_implementation.OPS.get(op_str, None)

    if not operator:
      raise errors.ParseError(u'Unknown operator {0:s} provided.'.format(
          self.operator))

    arguments.extend(self.args)
    expander = filter_implementation.FILTERS['ValueExpander']
    ops = operator(arguments=arguments, value_expander=expander)
    if not self.bool_value:
      if hasattr(ops, 'FlipBool'):
        ops.FlipBool()

    return ops


class ContextExpression(lexer.Expression):
  """Represents the context operator."""

  def __init__(self, attribute="", part=None):
    self.attribute = attribute
    self.args = []
    if part:
      self.args.append(part)
    super(ContextExpression, self).__init__()

  def __str__(self):
    return 'Context({0:s} {1:s})'.format(
        self.attribute, [str(x) for x in self.args])

  def SetExpression(self, expression):
    """Set the expression."""
    if isinstance(expression, lexer.Expression):
      self.args = [expression]
    else:
      raise errors.ParseError(
          u'Expected expression, got {0:s}.'.format(expression))

  def Compile(self, filter_implementation):
    """Compile the expression."""
    arguments = [self.attribute]
    for arg in self.args:
      arguments.append(arg.Compile(filter_implementation))
    expander = filter_implementation.FILTERS['ValueExpander']
    context_cls = filter_implementation.FILTERS['Context']
    return context_cls(arguments=arguments,
                       value_expander=expander)


class BinaryExpression(lexer.BinaryExpression):
  def Compile(self, filter_implementation):
    """Compile the binary expression into a filter object."""
    operator = self.operator.lower()
    if operator == 'and' or operator == '&&':
      method = 'AndFilter'
    elif operator == 'or' or operator == '||':
      method = 'OrFilter'
    else:
      raise errors.ParseError(
          u'Invalid binary operator {0:s}.'.format(operator))

    args = [x.Compile(filter_implementation) for x in self.args]
    return filter_implementation.FILTERS[method](arguments=args)


class Parser(lexer.SearchParser):
  """Parses and generates an AST for a query written in the described language.

  Examples of valid syntax:
    size is 40
    (name contains "Program Files" AND hash.md5 is "123abc")
    @imported_modules (num_symbols = 14 AND symbol.name is "FindWindow")
  """
  expression_cls = BasicExpression
  binary_expression_cls = BinaryExpression
  context_cls = ContextExpression

  tokens = [
      # Operators and related tokens
      lexer.Token('INITIAL', r'\@[\w._0-9]+',
                  'ContextOperator,PushState', 'CONTEXTOPEN'),
      lexer.Token('INITIAL', r'[^\s\(\)]', 'PushState,PushBack', 'ATTRIBUTE'),
      lexer.Token('INITIAL', r'\(', 'PushState,BracketOpen', None),
      lexer.Token('INITIAL', r'\)', 'BracketClose', 'BINARY'),

      # Context
      lexer.Token('CONTEXTOPEN', r'\(', 'BracketOpen', 'INITIAL'),

      # Double quoted string
      lexer.Token('STRING', '"', 'PopState,StringFinish', None),
      lexer.Token('STRING', r'\\x(..)', 'HexEscape', None),
      lexer.Token('STRING', r'\\(.)', 'StringEscape', None),
      lexer.Token('STRING', r'[^\\"]+', 'StringInsert', None),

      # Single quoted string
      lexer.Token('SQ_STRING', '\'', 'PopState,StringFinish', None),
      lexer.Token('SQ_STRING', r'\\x(..)', 'HexEscape', None),
      lexer.Token('SQ_STRING', r'\\(.)', 'StringEscape', None),
      lexer.Token('SQ_STRING', r'[^\\\']+', 'StringInsert', None),

      # Basic expression
      lexer.Token('ATTRIBUTE', r'[\w._0-9]+', 'StoreAttribute', 'OPERATOR'),
      lexer.Token('OPERATOR', r'not ', 'FlipLogic', None),
      lexer.Token('OPERATOR', r'(\w+|[<>!=]=?)', 'StoreOperator', 'CHECKNOT'),
      lexer.Token('CHECKNOT', r'not', 'FlipLogic', 'ARG'),
      lexer.Token('CHECKNOT', r'\s+', None, None),
      lexer.Token('CHECKNOT', r'([^not])', 'PushBack', 'ARG'),
      lexer.Token('ARG', r'(\d+\.\d+)', 'InsertFloatArg', 'ARG'),
      lexer.Token('ARG', r'(0x\d+)', 'InsertInt16Arg', 'ARG'),
      lexer.Token('ARG', r'(\d+)', 'InsertIntArg', 'ARG'),
      lexer.Token('ARG', '"', 'PushState,StringStart', 'STRING'),
      lexer.Token('ARG', '\'', 'PushState,StringStart', 'SQ_STRING'),
      # When the last parameter from arg_list has been pushed

      # State where binary operators are supported (AND, OR)
      lexer.Token('BINARY', r'(?i)(and|or|\&\&|\|\|)',
                  'BinaryOperator', 'INITIAL'),
      # - We can also skip spaces
      lexer.Token('BINARY', r'\s+', None, None),
      # - But if it's not "and" or just spaces we have to go back
      lexer.Token('BINARY', '.', 'PushBack,PopState', None),

      # Skip whitespace.
      lexer.Token('.', r'\s+', None, None),
      ]

  def StoreAttribute(self, string='', **kwargs):
    self.flipped = False
    super(Parser, self).StoreAttribute(string, **kwargs)

  def FlipAllowed(self):
    """Raise an error if the not keyword is used where it is not allowed."""
    if not hasattr(self, 'flipped'):
      raise errors.ParseError(u'Not defined.')

    if not self.flipped:
      return

    if self.current_expression.operator:
      if not self.current_expression.operator.lower() in (
          'is', 'contains', 'inset', 'equals'):
        raise errors.ParseError(
            u'Keyword \'not\' does not work against operator: {0:s}'.format(
                self.current_expression.operator))

  def FlipLogic(self, **unused_kwargs):
    """Flip the boolean logic of the expression.

    If an expression is configured to return True when the condition
    is met this logic will flip that to False, and vice versa.
    """
    if hasattr(self, 'flipped') and self.flipped:
      raise errors.ParseError(
          u'The operator \'not\' can only be expressed once.')

    if self.current_expression.args:
      raise errors.ParseError(
          u'Unable to place the keyword \'not\' after an argument.')

    self.flipped = True

    # Check if this flip operation should be allowed.
    self.FlipAllowed()

    if hasattr(self.current_expression, 'FlipBool'):
      self.current_expression.FlipBool()
      logging.debug(u'Negative matching [flipping boolean logic].')
    else:
      logging.warning(
          u'Unable to perform a negative match, issuing a positive one.')

  def InsertArg(self, string='', **unused_kwargs):
    """Insert an arg to the current expression."""
    # Note that "string" is not necessarily of type string.
    logging.debug(u'Storing argument: {0!s}'.format(string))

    # Check if this flip operation should be allowed.
    self.FlipAllowed()

    # This expression is complete
    if self.current_expression.AddArg(string):
      self.stack.append(self.current_expression)
      self.current_expression = self.expression_cls()
      # We go to the BINARY state, to find if there's an AND or OR operator
      return 'BINARY'

  def InsertFloatArg(self, string='', **unused_kwargs):
    """Inserts a Float argument."""
    try:
      float_value = float(string)
    except (TypeError, ValueError):
      raise errors.ParseError(u'{0:s} is not a valid float.'.format(string))
    return self.InsertArg(float_value)

  def InsertIntArg(self, string='', **unused_kwargs):
    """Inserts an Integer argument."""
    try:
      int_value = int(string)
    except (TypeError, ValueError):
      raise errors.ParseError(u'{0:s} is not a valid integer.'.format(string))
    return self.InsertArg(int_value)

  def InsertInt16Arg(self, string='', **unused_kwargs):
    """Inserts an Integer in base16 argument."""
    try:
      int_value = int(string, 16)
    except (TypeError, ValueError):
      raise errors.ParseError(
          u'{0:s} is not a valid base16 integer.'.format(string))
    return self.InsertArg(int_value)

  def StringFinish(self, **unused_kwargs):
    if self.state == 'ATTRIBUTE':
      return self.StoreAttribute(string=self.string)

    elif self.state == 'ARG':
      return self.InsertArg(string=self.string)

  def StringEscape(self, string, match, **unused_kwargs):
    """Escape backslashes found inside a string quote.

    Backslashes followed by anything other than [\'"rnbt.ws] will raise
    an Error.

    Args:
      string: The string that matched.
      match: the match object (instance of re.MatchObject).
             Where match.group(1) contains the escaped code.

    Raises:
      ParseError: When the escaped string is not one of [\'"rnbt]
    """
    if match.group(1) in '\\\'"rnbt\\.ws':
      self.string += string.decode('string_escape')
    else:
      raise errors.ParseError(u'Invalid escape character {0:s}.'.format(string))

  def HexEscape(self, string, match, **unused_kwargs):
    """Converts a hex escaped string."""
    logging.debug(u'HexEscape matched {0:s}.'.format(string))
    hex_string = match.group(1)
    try:
      self.string += binascii.unhexlify(hex_string)
    except TypeError:
      raise errors.ParseError(u'Invalid hex escape {0:s}.'.format(string))

  def ContextOperator(self, string='', **unused_kwargs):
    self.stack.append(self.context_cls(string[1:]))

  def Reduce(self):
    """Reduce the token stack into an AST."""
    # Check for sanity
    if self.state != 'INITIAL' and self.state != 'BINARY':
      self.Error(u'Premature end of expression')

    length = len(self.stack)
    while length > 1:
      # Precendence order
      self._CombineParenthesis()
      self._CombineBinaryExpressions('and')
      self._CombineBinaryExpressions('or')
      self._CombineContext()

      # No change
      if len(self.stack) == length:
        break
      length = len(self.stack)

    if length != 1:
      self.Error(u'Illegal query expression')

    return self.stack[0]

  def Error(self, message=None, _=None):
    # Note that none of the values necessarily are strings.
    raise errors.ParseError(
        u'{0!s} in position {1!s}: {2!s} <----> {3!s} )'.format(
            message, len(self.processed_buffer), self.processed_buffer,
            self.buffer))

  def _CombineBinaryExpressions(self, operator):
    for i in range(1, len(self.stack)-1):
      item = self.stack[i]
      if (isinstance(item, lexer.BinaryExpression) and
          item.operator.lower() == operator.lower() and
          isinstance(self.stack[i-1], lexer.Expression) and
          isinstance(self.stack[i+1], lexer.Expression)):
        lhs = self.stack[i-1]
        rhs = self.stack[i+1]

        self.stack[i].AddOperands(lhs, rhs)
        self.stack[i-1] = None
        self.stack[i+1] = None

    self.stack = filter(None, self.stack)

  def _CombineContext(self):
    # Context can merge from item 0
    for i in range(len(self.stack)-1, 0, -1):
      item = self.stack[i-1]
      if (isinstance(item, ContextExpression) and
          isinstance(self.stack[i], lexer.Expression)):
        expression = self.stack[i]
        self.stack[i-1].SetExpression(expression)
        self.stack[i] = None

    self.stack = filter(None, self.stack)


### FILTER IMPLEMENTATIONS
class BaseFilterImplementation(object):
  """Defines the base implementation of an object filter by its attributes.

  Inherit from this class, switch any of the needed operators and pass it to
  the Compile method of a parsed string to obtain an executable filter.
  """

  OPS = OP2FN
  FILTERS = {
      'ValueExpander': AttributeValueExpander,
      'AndFilter': AndFilter,
      'OrFilter': OrFilter,
      'IdentityFilter': IdentityFilter,
      'Context': Context}


class LowercaseAttributeFilterImplementation(BaseFilterImplementation):
  """Does field name access on the lowercase version of names.

  Useful to only access attributes and properties with Google's python naming
  style.
  """

  FILTERS = {}
  FILTERS.update(BaseFilterImplementation.FILTERS)
  FILTERS.update({'ValueExpander': LowercaseAttributeValueExpander})


class DictFilterImplementation(BaseFilterImplementation):
  """Does value fetching by dictionary access on the object."""

  FILTERS = {}
  FILTERS.update(BaseFilterImplementation.FILTERS)
  FILTERS.update({'ValueExpander': DictValueExpander})


