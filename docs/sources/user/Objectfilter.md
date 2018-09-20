## Generic Documentation

Classes to perform filtering of objects based on their data members.

Given a list of objects and a textual filter expression, these classes allow
you to determine which objects match the filter. The system has two main
pieces: A parser for the supported grammar and a filter implementation.

Given any complying user-supplied grammar, it is parsed with a custom lexer
based on GRR's lexer and then compiled into an actual implementation by using
the filter implementation. A filter implementation simply provides actual
implementations for the primitives required to perform filtering. The compiled
result is always a class supporting the Filter interface.

If we define a class called Car such as:

```python
class Car(object):
  def __init__(self, code, color="white", doors=3):
    self.code = code
    self.color = color
    self.doors = 3
```

And we have two instances:

```python
  ford_ka = Car("FORDKA1", color="grey")
  toyota_corolla = Car("COROLLA1", color="white", doors=5)
  fleet = [ford_ka, toyota_corolla]
```

We want to find cars that are grey and have 3 or more doors. We could filter
our fleet like this:

```python
  criteria = "(color is grey) and (doors >= 3)"
  parser = ContextFilterParser(criteria).Parse()
  compiled_filter = parser.Compile(LowercaseAttributeFilterImp)

  for car in fleet:
    if compiled_filter.Matches(car):
      print "Car %s matches the supplied filter." % car.code
```

The filter expression contains two subexpressions joined by an AND operator:

```
  "color is grey" and "doors >= 3"
```

This means we want to search for objects matching these two subexpressions.

Let's analyze the first one in depth "color is grey":
+ "color": the left operand specifies a search path to look for the data. This tells our filtering system to look for the color property on passed objects.
+ "is": the operator. Values retrieved for the "color" property will be checked against the right operand to see if they are equal.
+ "grey": the right operand. It specifies an explicit value to check for.

So each time an object is passed through the filter, it will expand the value
of the color data member, and compare its value against "grey".

Because data members of objects are often not simple datatypes but other
objects, the system allows you to reference data members within other data
members by separating each by a dot. Let's see an example:

Let's add a more complex Car class with default tire data:

```python
class CarWithTires(Car):
  def __init__(self, code, tires=None, color="white", doors=3):
    super(self, CarWithTires).__init__(code, color, doors)
    tires = tires or Tire("Pirelli", "PZERO")

class Tire(object):
  def __init__(self, brand, code):
    self.brand = brand
    self.code = code
```

And two new instances:
```python
  ford_ka = CarWithTires("FORDKA", color="grey", tires=Tire("AVON", "ZT5"))
  toyota_corolla = Car("COROLLA1", color="white", doors=5)
  fleet = [ford_ka, toyota_corolla]
```

To filter a car based on the tire brand, we would use a search path of
"tires.brand".

Because the filter implementation provides the actual classes that perform
handling of the search paths, operators, etc. customizing the behaviour of the
filter is easy. Three basic filter implementations are given:

+ BaseFilterImplementation: search path expansion is done on attribute names as provided (case-sensitive).
+ LowercaseAttributeFilterImp: search path expansion is done on the lowercased attribute name, so that it only accesses attributes, not methods.
+ DictFilterImplementation: search path expansion is done on dictionary access to the given object. So "a.b" expands the object obj to obj["a"]["b"]