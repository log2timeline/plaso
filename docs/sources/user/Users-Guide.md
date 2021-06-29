# User's Guide

### How to get started

First determine which version of Plaso is must suitable to your needs, for more
information see [Releases and roadmap](Releases-and-roadmap.md)

### Installing the packaged release

To get Plaso up and running quickly:

* [Docker](Installing-with-docker.md) for Linux, Mac OS and Windows.

Alternative options:

* [Fedora](Fedora-Packaged-Release.md)
* [MacOS](MacOS-Source-Release.md)
* [Ubuntu](Ubuntu-Packaged-Release.md)

If you run into problems installing, check out the [installation troubleshooting guide](Troubleshooting-installation-issues.md)

## Before we start

Please report all discovered bugs on the [issue tracker](https://github.com/log2timeline/plaso/issues).

To follow announcements from the Plaso team or send in generic inquiries or
discuss the tool:

* subscribe to the [log2timeline-discuss](https://groups.google.com/forum/#!forum/log2timeline-discuss) mailing list.
* join the Plaso channel part of the [open-source-dfir Slack community](https://open-source-dfir.slack.com/), more information can be found [here](https://github.com/open-source-dfir/slack).

### I know the good old Perl version

If you are one of those people that liked the old Perl version of log2timeline
but really would like to switch use all the nifty features of the Python
version. Fear not, [here](Log2Timeline-Perl-(Legacy).md) is a guide to help you
migrate.

## The tools

Though Plaso initially was created in mind to replace the Perl version of
log2timeline, its focus has shifted from a stand-alone tool to a set of modules
that can be used in various use cases. Fear not Plaso is not a developers only
project it also includes several command line tools, each with its specific
purpose. Currently these are:

* [image_export](Using-image_export.md)
* [log2timeline](Using-log2timeline.md)
* [pinfo](Using-pinfo.md)
* [psort](Using-psort.md)
* [psteal](Using-psteal.md)

Note that each tool can be invoked with the `-h` or `--help` command line flag
to display basic usage and command line option information.

### image_export

**image_export** is a command line tool to export file content from a storage
media image or device based on various filter criteria, such as extension
names, filter paths, file format signature identifiers, file creation date and
time ranges, etc.

### log2timeline

**log2timeline** is a command line tool to extract [events](Scribbles-about-events.md#what-is-an-event)
from individual files, recursing a directory (e.g. mount point) or storage
media image or device. log2timeline creates a Plaso storage file which can be
analyzed with the pinfo and psort tools.

The Plaso storage file contains the extracted events and various metadata about
the collection process alongside information collected from the source data. It
may also contain information about tags applied to events and reports from
analysis plugins.

### pinfo

**pinfo** is a command line tool to provide information about the contents of a
Plaso storage file.

### psort

**psort** is a command line tool to post-process Plaso storage files. It allows
you to filter, sort and run automatic analysis on the contents of Plaso storage
files.

### psteal

**psteal** is a command line tool that combines the functionality of
log2timeline and psort.

