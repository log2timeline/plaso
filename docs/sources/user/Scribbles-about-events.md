# Scribbles about events

This page contains some scribbles about events. It contains information about:

* What is an event?
* How can an event be defined?
* How are events defined in Plaso?

## What is an event?

From [Wikipedia - Event (computing)](https://en.wikipedia.org/wiki/Event_%28computing%29)

> In computing, an event is an action or occurrence detected by the program that may be handled by the program. Typically events are handled synchronously with the program flow, that is, the program has one or more dedicated places where events are handled, frequently an event loop. Typical sources of events include the user (who presses a key on the keyboard, in other words, through a keystroke). Another source is a hardware device such as a timer. Any program can trigger its own custom set of events as well, e.g. to communicate the completion of a task.

This definition slightly differs on how the term event is used in digital
forensics, where the term event is typically used broader, namely to define
an action or occurrence on a digital device or by a program.

## How can an event be defined?

An event consists of the following types of information:

* date and time or duration of the event (event time), which can be unknown if we know the event happened but not when;
* an indication of what the event time represents such as Creation Time or Program Execution Duration;
* the source of the event, such as the Windows Application Event Log C:\Windows\System32\config\AppEvent.evt or specific lines in the /var/log/messages;
* data specific to the event, such as the path of the executable file and arguments in case of a process execution event;
* contextual information about the event, such as the hostname of the system on which the event occurred or the identifier of the user account under which the event occurred.

A more abstract analyst view on how an event can be defined is:

* When or for how long this event happened (event time)
* Who/what did an action for the event to happen (actor or subject)
* What was the action that happened (action or predicate)
* Who/what affected the action (object)
* Where did we learn from that the event happened (event source)

### Time-less events

Based on our definition an event technically should have a date or time (or
duration). However there are cases where we know an action happened but have no
indication of when.

### Different conceptual levels of events

Conceptually there are different levels of events, for example a log-in event
could describe when a user logged into a specific account. However this more
conceptual (higher-level) event could entail many more system-level events, such
as the user generated keystrokes by typing their password, the operating system
validating the password and stopping the screensaver process.

Since Plaso operates on storage media and files, which more generally is
referred to as the source data, the lowest-level events are referred to as
source-level events. For example a line in syslog representing, or a file entry
creation.

Multiple source-level events can make up higher-level events. For example
a processess execution log file (source) could have process start and stop
events. However these events could be combined into a single process execution
(duration) event.

The relevance of lower or higher conceptual levels of events highly depends on
the investigative questions you are trying to answer. Plaso's goal is to extract
events as closest to the source as possible. Analysis plugins then can be used
to derive higher-level conceptual events from them.

Some event related terminology used in the context of Plaso:

* source-level event; events as closely to their representation in the source data;
* system-level event; operating system events that can be derived from source-level events;
* user-level event; user attributable events that can be derived from system-level or source-level events.

## How are events defined in Plaso?

Events in Plaso consist of multiple parts:

* [event data](https://github.com/log2timeline/plaso/blob/main/plaso/containers/events.py)
* [event data stream](https://github.com/log2timeline/plaso/blob/main/plaso/containers/events.py)
* [event](https://github.com/log2timeline/plaso/blob/main/plaso/containers/events.py)
* [event tag](https://github.com/log2timeline/plaso/blob/main/plaso/containers/events.py)

### Event (object)

Originally Plaso's event (object) also contained the event data and event
data stream information. This information was moved to separate attribute
containers (object) to reduce duplication of information across multiple
events. An event (object) typically has:

* a date and time (event time)
* an indication of what the event time represents
* a reference to the event data

#### Event date and time

Plaso internally uses a timestamp to represent the event time. This is a 64-bit
signed integer that contains the number of microseconds since January 1, 1970
00:00:00 UTC. A negative timestamp represents that the event happened before
its reference date (or [epoch](https://en.wikipedia.org/wiki/Epoch_(reference_date))).

* An event spanning a duration is currently not supported
* Time-less events currently overload timestamp 0

As of 20210511 Plaso supports "dynamic time" which preserves the "datetime
storage granularity" and "datetime value granularity" of the event time as
stored in the source. For this Plaso now represent event time as an
[dfDateTime](https://github.com/log2timeline/dfdatetime) object. Plaso's
timestamp representation is kept for backward compatibility for now but will
be eventually be replaced by dfDateTime's internal normalized timestamp.

Dynamic time allows for a HFS+ timestamp to be represented as
"YYYY-MM-DDTHH:MM:SS" and an NTFS filetime timestamp as
"YYYY-MM-DDTHH:MM:SS.#######", but also a semantic representation such as
"Not set" or "Infinite".

For more details on "datetime storage granularity" and "datetime value
granularity" see [accuracy and precision](https://dfdatetime.readthedocs.io/en/latest/sources/Date-and-time-values.html#accuracy-and-precision).

### Event data

Plaso stores various pieces of information related to the event in an event
data attribute container (object). 

* data type to distinguish between different types of event data;
* information about which Plaso parser generated the event data;
* offset in the event data stream of the raw data where the event originates from;
* database query where the event originates from;
* other data type specific attributes.

Note that event data is currently free form. Work is in progress to make
a more formal specification. For more details see: https://github.com/log2timeline/plaso/issues/2129

Note that offset and query might move to a more formal origin specifier. For
more details see: https://github.com/log2timeline/plaso/issues/2993

#### Event data type

The event data type is a unique indicator of the type of event data, such as
`windows:lnk:link`.

Note that event data type is currently free form. Work is in progress to make
a more formal specification. For more details see: https://github.com/log2timeline/plaso/issues/2129

### Event data stream

Plaso stores various pieces of information related to the data stream from
which event data originates in an event data stream attribute container
(object). Currently an event data stream consist of:

* a [dfVFS path specification](https://dfvfs.readthedocs.io/en/latest/sources/Path-specifications.html) that specifies the location of the data stream within a storage media image and/or as a file on-disk
* a MD5, SHA-1, SHA-256 digest hash of the data stream
* matches of Yara signatures

