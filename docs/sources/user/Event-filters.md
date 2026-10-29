# Event filters

Event filters are used to:

* selectively export events;
* selectively analyze events;
* apply a label to events in the tagging analysis module.

Tools that have event filter support:

* [psort](Using-psort.md#filtering)

## How do event filters work

An event filter is constructed in the following way:

```
EXPRESSION BOOLEAN_OPERATOR EXPRESSION
```

Where each expression is:

```
ATTRIBUTE [not] OPERATOR [not] VALUE
```

Where "not" is only supported by some operators, see
[negative matching](#negative-matching).

Each expression can also be a collection of expressions and boolean operators
enclosed in a parenthesis.

```
EXPRESSION BOOLEAN_OPERATOR (EXPRESSION BOOLEAN_OPERATOR EXPRESSION)
```

The following boolean operators are supported:

* **and**
* **or**
* **&&** (and)
* **||** (or)

The boolean operators "and" and "or", the operator keywords, such as
"contains", and the keyword "not" are case insensitive, for example `AND`,
`CONTAINS` and `NOT` are also supported.

The following keywords are available:

Operator | Notes
---- | ----
equals | Determine if the attribute is equal to the value, meaning that both parts need to be exactly the same in order for this to match.
`is` | Same as equals.
`==` | Same as equals.
`!=` | Negative matching of equals, that is it checks if it is not equal to the value (same as "not is")
`contains` | If the attribute is a string it checks if the lowercase version of the value is in the lowercase value of the attribute. That is this is a case insensitive substring match. If the attribute is a list, such as `strings`, it checks if the value is one of the list elements. That is this is a case sensitive exact match on the individual elements. Also see the [path value helper](#path-value-helper).
`>` | Checks if the attribute is greater than the value.
`>=` | Checks if the attribute is greater than or equal to the value.
`<` | Checks if the attribute is less than the value.
`<=` | Checks if the attribute is less than or equal to the value.
`inset` | Checks if the attribute is contained in the value. That is this is a case sensitive substring match of the attribute in the value, for example `data_type inset 'fs:stat:ntfs'` matches if the data type is `fs:stat`. Both the attribute and the value need to be strings.
`regexp` | A case sensitive regular expression is compiled from the value and it is searched for in the attribute. Note that only a limited set of escape sequences is supported, see [values](#values).
`iregexp` | Same as the regexp above, except the regular expression is compiled as case-insensitive.

To compare the `timestamp` attribute use the
[date and time value helper](#date-and-time-value-helper), for example
`timestamp > DATETIME("2020-12-23T12:34:56")`. An integer or string value is
still converted to a date and time value, but this implicit conversion is
deprecated.

**Note that as of 20190512 special event attributes like 'message', 'source',
'source_short', 'source_long' and 'sourcetype' are considered output fields
and are no longer expanded in the event filter.**

**Note that as of 20230108 the 'parser' event attribute is considered an output
field and is discouraged to be used in the event filter. As of 20230724 the
'parser' event attribute has been removed.**

### Negative matching

The keyword "not" can be placed before or after the `contains`, `equals`,
`inset` and `is` operators to perform a negative matching, for example
`filename not contains 'temp'` or `filename contains not 'temp'`. The other
operators do not support "not", use the opposite operator instead, for example
`!=` instead of `not ==` or `<=` instead of `not >`.

## Example event filter expressions

```
data_type is 'syslog:line' and message_body contains 'root'
```

This event filter applies to all events where:

* the event has data type 'syslog:line' (case sensitive) and;
* the message_body attribute contains the substring 'root' (case insensitive).

```
data_type is 'windows:evtx:record' and strings contains 'Administrator'
```

This event filter applies to all events where:

* the event has data type 'windows:evtx:record' (case sensitive) and;
* one of the elements of the strings attribute is 'Administrator' (case sensitive).

## Event attributes

An event filter can use the attributes of the event data, which differ per
data type, and the following attributes:

Attribute | Notes
---- | ----
`timestamp` | Date and time of the event. `date`, `datetime` and `time` are aliases of `timestamp`.
`timestamp_desc` | Description of the timestamp of the event.
`tag` | Labels of the event tag, for example `tag contains 'browser_search'`.
`file_entropy`, `md5_hash`, `sha1_hash`, `sha256_hash`, `yara_match` | Attributes of the event data stream, which are only set if the corresponding analyzer was enabled during extraction.

Attribute names that contain a `.`, such as `path_spec.vss_store_number`, are
not supported. The `path_spec` attribute of the event data stream and the
former `pathspec` name cannot be used to filter on the location the event was
extracted from.

## Values

The following values are supported:

Value | Notes
---- | ----
String | Enclosed in single or double quotes, for example `'root'` or `"root"`.
Integer | A decimal integer, for example `4624`, or a hexadecimal integer prefixed with `0x`, for example `0x10`. Note that currently only the digits 0 to 9 are supported in a hexadecimal integer.
Floating-point | A decimal number with a fractional part, for example `1.5`.
Date and time | See the [date and time value helper](#date-and-time-value-helper).
Path | See the [path value helper](#path-value-helper).

Quoted strings, including those of the `regexp` and `iregexp` operators,
support the following escape sequences: `\\`, `\'`, `\"`, `\r`, `\n`, `\b`,
`\t` and `\xHH`, where HH is the hexadecimal value of an ASCII character, for
example `\x41` for "A". Note that `\b` is a backspace character, also in
regular expressions. The escape sequences `\.`, `\w` and `\s` are passed on
as-is for use in regular expressions. Other escape sequences, such as `\d`, are
not supported, use a character class such as `[0-9]` instead.

## Value type helpers

As of 20201123 value type helpers were introduced to ensure certain types are
handled consistently. The following value type helpers are currently supported:

* Date and time value helper

### Date and time value helper

The date and time value helper is:
```
DATETIME(int|str)
```

It supports 2 different types of arguments, either:

* an integer containing a POSIX timestamp in microseconds
* an ISO 8601 date and time string. Note that more common forms of ISO 8601 string are supported but not all. The maximum supported granularity is microseconds.

For example:

```
DATETIME(0)
DATETIME("2020-12-23T12:34:56.789")
```

### Path value helper

The path helper is:
```
PATH(str)
```

It allows to check a path on a per path segment basis, using `/` as the path
segment separator. The path segments are compared case sensitive. The path
helper can be used with the `contains` and `==` operators.

For example the path helper:
```
filename contains PATH('bin')
```

Will match `/usr/bin` and `/usr/local/bin` but not `/usr/local/sbin` or
`/usr/BIN`.

The path helper can contain multiple path segments. A leading `/` only matches
from the start of the path. For example `filename contains PATH('local/bin')`
and `filename contains PATH('/usr/local')` both match `/usr/local/bin/ls`, but
`filename contains PATH('/local/bin')` does not.

```
filename == PATH('/usr/local/bin/ls')
```

Will match `/usr/local/bin/ls` and `/usr//local/bin/ls`.

