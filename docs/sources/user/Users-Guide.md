# User's Guide

## Getting start with Plaso

Getting started with Plaso can be challenging at first. This page describes
some of the steps we recommend taking.

### I just want to run Plaso or log2timeline

If you just want to run Plaso we stronly recommend to use a packaged release
unless you are the adventurous type that is familiar with troubleshooting
installation issues.

Have a look at the information below to get familiar with running the Plaso
tools, such as log2timeline.

We also strongly recommend to first read up on various tradeoffs of timeline
analysis:

* [Targeted timelines - Part I](https://osdfir.blogspot.com/2013/02/targeted-timelines-part-i.html)
* [Pearls and pitfalls of timeline analysis](https://osdfir.blogspot.com/2021/10/pearls-and-pitfalls-of-timeline-analysis.html)

### I know the good old Perl version

If you are one of those people that liked the old Perl version of log2timeline
but really would like to switch use all the nifty features of the Python
version. Fear not, [here](Log2Timeline-Perl-(Legacy).md) is a guide to help you
migrate.

### I want to develop Plaso

There are various ways to develop with Plaso. We expect the more common use
case that you would like to extend Plaso by adding a parser or plugin or
equivalent. To get started have a look at the [Developers guide](../developer/Developers-Guide.md).

## Releases

Plaso comes in 2 different forms of releases:

* a packaged release; found on the [releases page](https://github.com/log2timeline/plaso/releases)
* a development release; found in the [git repository](https://github.com/log2timeline/plaso)

**Note that the development release is for development, expect frequent updates
and potential breakage.**

If you do not plan to develop or live on the edge, regarding Plaso, we highly
recommend sticking with the packaged release. We strongly recommend using a
version of Plaso no older than 6 months.

### Installing the packaged release

To get Plaso up and running quickly:

* [Docker](Installing-with-docker.md) for Linux, Mac OS and Windows.

Alternative options:

* [Fedora](Fedora-Packaged-Release.md)
* [MacOS](MacOS-Source-Release.md)
* [Ubuntu](Ubuntu-Packaged-Release.md)

If you run into problems installing, check out the [installation troubleshooting guide](Troubleshooting-installation-issues.md)

## Issues or questions

To follow announcements from the Plaso team or send in generic inquiries or
discuss the tool:

* subscribe to the [log2timeline-discuss](https://groups.google.com/forum/#!forum/log2timeline-discuss) mailing list.
* join the Plaso channel part of the [open-source-dfir Slack community](https://open-source-dfir.slack.com/), more information can be found [here](https://github.com/open-source-dfir/slack).

Please be mindful of people's time:

* Do not be that pushy person that demands help now or is asking for an ETA of a feature. All contributions are best effort.
* Do not assume things are broken just because you cannot get it to work. Most issues we see are caused by people not following the documented instructions.
* Always try to solve the issue yourself first. Also see [troubleshooting](../Troubleshooting.md).
* In your communication be as specific and detailed as possible. Assume others have no context about what you are asking them and reduce the amount of follow up questions others have to do to understand you.

Please report all discovered bugs on the [issue tracker](https://github.com/log2timeline/plaso/issues).

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
