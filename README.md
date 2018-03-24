## plaso (Plaso Langar Að Safna Öllu)

*super timeline all the things*

In short, plaso is a Python-based backend engine for the tool 
[log2timeline](http://plaso.kiddaland.net "Plaso home of the super timeline").

### A longer version

log2timeline is a tool designed to extract timestamps from various files found 
on a typical computer system(s) and aggregate them.

The initial purpose of plaso was to collect all timestamped events of interest 
on a computer system and have them aggregated in a single place for computer 
forensic analysis (aka Super Timeline).

However plaso has become a framework that supports:

* adding new parsers or parsing plug-ins;
* adding new analysis plug-ins;
* writing one-off scripts to automate repetitive tasks in computer forensic analysis or equivalent.

And is moving to support:

* adding new general purpose parses/plugins that may not have timestamps associated to them;
* adding more analysis context;
* tagging events;
* allowing more targeted approach to the collection/parsing.

### Project status

[Travis-CI](https://travis-ci.org/) | [AppVeyor](https://ci.appveyor.com) | [Codecov](https://codecov.io/)
--- | --- | --- 
[![Build Status](https://travis-ci.org/log2timeline/plaso.svg?branch=master)](https://travis-ci.org/log2timeline/plaso) | [![Build status](https://ci.appveyor.com/api/projects/status/g3x5ylegjjo61p4m?svg=true)](https://ci.appveyor.com/project/joachimmetz/plaso) | [![codecov](https://codecov.io/gh/log2timeline/plaso/branch/master/graph/badge.svg)](https://codecov.io/gh/log2timeline/plaso)

### Also see

* [Homepage](https://github.com/log2timeline/plaso)
* [Downloads](https://github.com/log2timeline/plaso/releases)
* [Documentation](https://github.com/log2timeline/plaso/wiki)

