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

Each expression can also be a collection of binary expressions and operators
enclosed in a parenthesis.

```
EXPRESSION BOOLEAN_OPERATOR (EXPRESSION BINARY_OPERATOR EXPRESSION)
```

The following boolean operators are supported:

* **and**
* **or**
* **&&** (and)
* **||** (or)

The following keywords are available:

Operator | Notes
---- | ----
equals | Determine if the attribute is equal to the value, meaning that both parts need to be exactly the same in order for this to match.
`is` | Same as equals.
`==` | Same as equals.
`!=` | Negative matching of equals, that is it checks if it is not equal to the value (same as "not is")
`contains` | If the value is a string it checks if the lowercase version of the value is in the lowercase value of the attribute. That is this is a case insensitive substring match.
`>` | Checks if the value is greater than the attribute. If the attribute is date or timestamp and the value is an integer it compares against the timestamp attribute. If the attribute is date and the value is a string it will convert the string value to an integer and then make the comparison.
`>=` | Checks if the value is greater or equal than the attribute. If the attribute is date or timestamp the same behavior as in ">" is observed.
`<` | Checks if the value is less than the attribute. If the attribute is date or timestamp the same checks are made as in ">", except the comparison is to whether or not the value is less or equal than the supplied date.
`<=` | Checks if the value is less or equal than the value. If the attribute is timestamp or date same behavior as in "<" is applied.
`inset` | Checks if the values are all in the set of attributes.
`regexp` | A case sensitive regular expression is compiled from the value and it is compared against the attribute. The regular expression is somewhat limited, the only escaped strings that are supported are: '"rnbt.ws
`iregexp` | Same as the regexp above, except the regular expression is compiled as case-insensitive.

And for negative matching the keyword "not" in front of any of these keywords
is also supported. That is to say if each of these operators is preceded with
the keyword "not" a negative matching is performed.

**Note that as of 20190512 special event attributes like 'message', 'source',
'source_short', 'source_long' and 'sourcetype' are considered output fields
and are no longer expanded in the event filter.**

**Note that as of 20230108 the 'parser' event attribute is considered an output
field and is discouraged to be used in the event filter.**

## Example event filter expressions

```
parser is 'syslog' and body contains 'root'
```

This event filter applies to all events where:

* the event was produced by the parser named 'syslog' (case sensitive) and;
* the body attribute contains the substring 'root' (case insensitive).

Use "log2timeline --info" to retrieve a list of the names of all the available
parsers. Or use the ```pinfo.py timeline.plaso``` to see a list of all parsers that
were used to produce the output in the storage file.

```
parser contains 'firefox' AND pathspec.vss_store_number > 0
```

* The parser name contains the word "firefox";
* The event was extracted from a Volume Shadow Snapshot (VSS).

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
* an ISO 8601 date and time string. Note that more common forms of ISO 8601 string are supported but all. The maximum supported granularity is microseconds.

For exeample:

```
DATETIME(0)
DATETIME("2020-12-23T12:34:56.789")
```

### Path value helper

The path helper is:
```
PATH(str)
```

It allows to check a path on a per path segment basis.

For example the path helper:
```
path contains PATH('bin')
```

Will match `/usr/bin` and `/usr/local/bin` but not `/usr/local/sbin`.

## References

* [log2timeline filtering 101](http://blog.kiddaland.net/2012/12/log2timeline-filtering-101.html)

