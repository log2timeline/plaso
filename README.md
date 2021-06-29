## Plaso (Plaso Langar Að Safna Öllu) - super timeline all the things

Plaso (Plaso Langar Að Safna Öllu), or *super timeline all the things*, is a
Python-based engine used by several tools for automatic creation of timelines.
Plaso default behavior is to create super timelines but it also supports
creating more [targeted timelines](http://blog.kiddaland.net/2013/02/targeted-timelines-part-i.html).

These timelines support digital forensic investigators/analysts, to correlate
the large amount of information found in logs and other files found on an
average computer.

### A longer version

The initial purpose of Plaso was to collect all timestamped events of interest 
on a computer system and have them aggregated in a single place for computer 
forensic analysis (aka Super Timeline).

However Plaso has become a framework that supports:

* adding new parsers or parsing plug-ins;
* adding new analysis plug-ins;
* writing one-off scripts to automate repetitive tasks in computer forensic analysis or equivalent.

And is moving to support:

* adding new general purpose parses/plugins that may not have timestamps associated to them;
* adding more analysis context;
* tagging events;
* allowing more targeted approach to the collection/parsing.

### Also see

* [Homepage](https://github.com/log2timeline/plaso)
* [Downloads](https://github.com/log2timeline/plaso/releases)
* [Documentation](https://plaso.readthedocs.io)
* Contact information:
  * Plaso channel on [Open Source DFIR Slack community](https://github.com/open-source-dfir/slack)
  * Mailing list for general discussions: [log2timeline-discuss](https://groups.google.com/forum/#%21forum/log2timeline-discuss)
  * Mailing list for development: [log2timeline-dev](https://groups.google.com/forum/#%21forum/log2timeline-dev)
