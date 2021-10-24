# Internals

Plaso is developed with the following operations in mind.

* Preprocessing
* Collection and extraction
* Analysis
* Output and formatting

Different Plaso tools run different operations. These operations can be run in
a single process or in multiple worker processes.

Also see: [Architecture overview](https://docs.google.com/drawings/d/1WzB3rz50Kf89HtGQ0y28ozPCfTvMo_GVTCMpgAOziy8/preview)

## Preprocessing

The preprocessing operation runs prior to other processing, such as collection
and extraction. The purpose of the preprocessing operation is to examine the
source data and determine which operating systems it contains and determine
operating system and application specific information that can be used to
augment processing. Examples of what the preprocessing operation collects are:

* hostnames;
* time zone information;
* local user accounts, including the user name and path to their user (or home) directory;
* information to enrich output, such as environment variables and Windows EventLog message (template) strings.

The preprocessing operation stores this information in a runtime object
referred to as the knowledge base.

The [preprocessors mediator](https://plaso.readthedocs.io/en/latest/sources/api/plaso.preprocessors.html#module-plaso.preprocessors.mediator)
is used for preprocessing plugins to interface with Plaso core components such
as the knowledge base and storage.

### Knowledge base

The knowledge base contains operating system and application information that
can be used to augment processing, such as extraction, analysis, and output and
formatting.

## Collection and extraction

### Collection

The collection operation recurses over the source data. First Plaso uses the
[dfVFS volume scanner](https://dfvfs.readthedocs.io/en/latest/sources/developer/Helpers.html#volume-scanner)
to determine if the source data is a storage media image, a directory or file.
Additional required information such as which partitions or volume shadow
snapshots to process is obtained from the user if needed.

The next part of the collection operation can be divided into two different
approaches:

* "kitchen sink", which recursively goes through a storage media image or directory and collects data from every file.
* "targeted", which collects data from a files that are included by [collection filters](https://plaso.readthedocs.io/en/latest/sources/user/Collection-Filters.html).

The collection operation also handles archives, such as .tar or .zip, and
compressed streams such as .log.gz.

### Extraction

The extraction operation does most of the heavy lifting. Plaso supports
different types of extaction:

* analyzers, which are used to calculate an integrity hash like SHA-256 or scan file content with YARA rules;
* parsers (and parser plugins), which are used to extract events from supported data formats.

The [parsers mediator](https://plaso.readthedocs.io/en/latest/sources/api/plaso.parsers.html#module-plaso.parsers.mediator)
is used for parsers (and parser plugins) to interface with Plaso core
components such as the knowledge base and storage.

## Analysis

The analysis operation (not to be conflated with analyzers) iterates over
extracted events (and related objects) and tags events of interest.

The [analysis mediator](https://plaso.readthedocs.io/en/latest/sources/api/plaso.analysis.html#module-plaso.analysis.mediator)
is used for analysis plugins to interface with Plaso core components such as
the knowledge base and storage.

## Output and formatting

The output and formatting operation iterates over extracted events (and related
objects) and outputs them in human readable or machine processable formats. Here
Plaso uses:

* output modules, to generate output in a specific format;
* event formatters, to format indivudual events;
* field formatters, to format individual event values.

The log2timeline.pl l2tcsv format introduced the "desc" and "short" fields that
provide a description of interpreted results or the content of a corresponding
log line. Plaso uses message formatters to generate such fields.

For more information see: [output and formatting](https://plaso.readthedocs.io/en/latest/sources/user/Output-and-formatting.html)

The [output mediator](https://plaso.readthedocs.io/en/latest/sources/api/plaso.output.html#module-plaso.output.mediator)
is used for output modules and formatters to interface with Plaso core
components such as the knowledge base and storage.

## Core components

### Storage

TODO: describe session and task store
TODO: describe attribute containers
TODO: describe different storage back-ends

The storage role takes care of reading events from the storage queue, filling up
 a buffer and then flushing that buffer to a disk.

The storage portion of the tool also serves as an API to the storage file for
later processing and extracting events from the storage file. The storage
library takes care of parsing metadata structures stored inside the storage
file, tagging and grouping information and to extract fully sorted events out
of the storage.
