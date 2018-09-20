**TODO update the information on this page**

Plaso is built with the following roles in mind.

* Preprocessing
* Collection
* Extraction (Worker)
* Storage

Each front-end may decide to run all of these roles in a single thread, multi-thread or on multiple computers.

Also see: [Architecture overview](https://docs.google.com/drawings/d/1WzB3rz50Kf89HtGQ0y28ozPCfTvMo_GVTCMpgAOziy8/preview)

## Preprocessing

This role needs to be run prior to all other processing. The purpose of this role is to go over an image or a mount point and determine which OS it belongs to and collect important information that can be used to both augment parsing and make it more accurate. Examples of what the pre-processing process should collect:

* Timezone information.
* Enumerate all users and their paths.
* Hostname.
* Default applications, as in default browser, etc.
* OS specific items that make future processing simpler (as in current control set in registry, code page used, etc.)

## Collection

The purpose of the collection role is to go over the image, directory or mount point and find all files that the tool can process. This process should try to limit memory usage and processing since it's purpose is to be quicker than the workers, that is that it can detect and fill the processing queue quicker than the workers emptying it.

The collection process gets a bit more complex when dealing with VSS snapshots, since that requires some processing to limit dual processing of files that have not changed between snapshots.

* In essence the collection can be divided into three different scenarios:
* In it's simplest term just "take everything" the collection process recursively goes through either a mount point or an image file and collects every file discovered.
* During recursive scan if VSS are to be parsed a hash is calculated based on the four timestamps of every file and during the collection phase from the VSS image the hash value is compared to already existing hashes for that file. If the file has not previously been collected it is included, otherwise it is skipped.
* Targeted collection: a set of file paths is defined and the tool only collects the files that fit that pattern.

## Extraction

This is the main work horse of the application. The worker, or workers take care of monitoring the process queue and then process each file that gets in there. Processing a file means:

* Classify it (as in determine which file type this is).
* Determine if there are parsers that are potentially capable of parsing it.
* Run the file through those parsers and extract all events from it.
* If there is a filter defined send that event through the filter (discard event if it does not pass through the filter).
* Send extracted events to the storage queue.
* Determine if this file contains other files within it that can be processed/extracted, and process them as well, e.g. files within compressed containers, etc.

## Storage

The storage role takes care of reading events from the storage queue, filling up a buffer and then flushing that buffer to a disk.

The storage portion of the tool also serves as an API to the storage file for later processing and extracting events from the storage file. The storage library takes care of parsing metadata structures stored inside the storage file, tagging and grouping information and to extract fully sorted events out of the storage.