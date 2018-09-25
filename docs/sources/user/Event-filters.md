# Event Filters
Event filters can be used both during the extraction phase and in the post-processing stage of the tool.

Tools that have event filter support:
 + [psort](Using-psort.md#filtering)

The generic documentation of the filter language can be found [here](Objectfilter.md)

The filters are evoked differently depending on the tool, consult each tool's documentation about how that is achieved.

When the filters were originally introduced a [blog post](http://blog.kiddaland.net/2012/12/log2timeline-filtering-101.html) was made explaining them. Since this blog post was introduced there have been some changes made to the filtering that make it a bit out-of-date, yet a good resource to read over.

## How do the filters work

A query is constructed in the following way:

```
EXPRESSION BOOLEAN_OPERATOR EXPRESSION
```

Where each expression is:

```
ATTRIBUTE [not] OPERATOR [not] VALUE
```

Each expression can also be a collection of binary expressions and operators enclosed in a parenthesis.

```
EXPRESSION BOOLEAN_OPERATOR (EXPRESSION BINARY_OPERATOR EXPRESSION)
```

The following boolean operators are supported:

+ **and**
+ **or**
+ **&&** (and)
+ **||** (or)

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

And for negative matching the keyword "not" in front of any of these keywords is also supported. That is to say if each of these operators is preceded with the keyword "not" a negative matching is performed.

## Example Queries

This means that a query like this can be constructed:

```
parser is 'syslog' and message contains 'root'
```

What this filter does is to filter out all events with the following logic:
+ parser attribute equals to "syslog", which means that it will only contain events that are parsed by the syslog parser (remember this is an exact match, case sensitive).
+ message attribute contains the word 'root' (case-insensitive search) somewhere in it.

One thing to keep in mind is that although you can use the filters to select which parsers are chosen during collection/processing phase (that is while running log2timeline) it is highly suggested to rather use the ``--parsers`` parameter. The reason for that is that during the extraction phase the filters work post extraction. That is each parser will be loaded, used to process a file and then extract all the relevant events. Just before being sent to the storage layer filters will be applied and events dropped. Filters during extraction phase should therefore rather be to reduce common false positives or noise than to eliminate a particular parser from being run.

Another version of this filter query would be:

```
parser contains 'sysl' and message contains 'root'
```

The difference here is the case in-sensitive matching against the parser name, and instead of being an exact match it's a substring match. The parser name here refers to the classes NAME attribute, which is always lowercase and often contains the name of the source. Use "log2timeline --info" to see the name of all the available parsers. Or use the ```pinfo.py test.plaso``` to see a list of all parsers that were used to produce the output in the storage file.

It is worth noting here that the message attribute is not stored in the EventObject. That is a calculated attribute based on the definition of a formatter. That means that for each evaluation the message string is calculated before it is being evaluated against the condition, thus most likely slowing down the filtering quite a bit. If you can avoid the use of the "message" attribute and rather construct the filter to use only attributes that are stored inside the EventObject the filter query runs faster.

```
parser is not 'syslog' and source_short is 'LOG'
```

+ The parser attribute is **NOT 'syslog'**, which means this triggers on all events that do not come from the syslog parser.
+ source_short is LOG means that the source_short equals to LOG.
+ Combined this means that the filter will trigger on all events that have the source_short set to LOG and are not produced by the syslog parser.

```
source_short is 'LOG' AND (timestamp_desc CONTAINS 'written' OR timestamp_desc CONTAINS 'visited')
```

+ The source_short is LOG.
+ The timestamp description contains either the word "written" or "visited".

```
parser contains 'syslog' AND (date > '2012-12-04' AND date < '2015-01-01')
```

+ The parser name contains the word "syslog", which is a case insensitive match against the word.
+ The time of the event is between 2012-12-04 and 2015-01-01.

```
source_long is 'Made up Source' AND message iregexp 'bad, bad thing [\sa-zA-Z\.]+ evil'
```

+ The source_long is exactly "Made up Source" (remember exactly, so we are talking about case sensitive matching).
+ message attribute has a text that matches the following regular case-insensitive regular expression: "**bad, bad thing [\sa-zA-Z\.]+ evil**".

```
parser contains 'firefox' AND pathspec.vss_store_number > 0
```

+ The parser is "FirefoxHistoryParser" (contains the word "firefox").
+ This event is extracted from VSS instead of from a regular file.