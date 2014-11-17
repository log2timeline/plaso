# plaso (Plaso Langar Að Safna Öllu) #
*super timeline all the things*

Various statistics for the tool:

Code Coverage: [![Coverage
Status](https://img.shields.io/coveralls/log2timeline/plaso.svg)](https://coveralls.io/r/log2timeline/plaso?branch=master)

Build Status: [![Build
Status](https://travis-ci.org/log2timeline/plaso.svg?branch=master)](https://travis-ci.org/log2timeline/plaso)

In short, plaso is a Python-based backend engine for the tool [log2timeline] (http://plaso.kiddaland.net "Plaso home of the super timeline").

## A longer version ##

log2timeline is a tool designed to extract timestamps from various files found on a typical computer system(s) and aggregate them.

The initial purpose of plaso was to collect all timestamped events of interest on a computer system and have them aggregated in a single place for computer forensic analysis (aka Super Timeline).

However plaso has become a framework that supports:
* adding new parsers or parsing plug-ins;
* adding new analysis plug-ins;
* writing one-off scripts to automate repetitive tasks in computer forensic analysis or equivalent.

And is moving to support:
* adding new general purpose parses/plugins that may not have timestamps associated to them;
* adding more analysis context;
* tagging events;
* allowing more targeted approach to the collection/parsing.

Also see:
* [log2timeline] (http://plaso.kiddaland.net/usage/log2timeline/ "Usage for log2timeline")
* [Project documentation] (http://plaso.kiddaland.net/ "Tool's main documentation site")
* [Downloads] (https://googledrive.com/host/0B30H7z4S52FleW5vUHBnblJfcjg/ "Download the latest version")

