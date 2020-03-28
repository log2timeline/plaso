# Releases and Roadmap

Plaso comes in 2 different forms of releases:

* a packaged release; found on the [releases page](https://github.com/log2timeline/plaso/releases)
* a development release; found in the [git repository](https://github.com/log2timeline/plaso)

**Note that the development release is for development, expect frequent updates and potential breakage.**

If you do not plan to develop or live on the edge, regarding Plaso, we highly
recommend sticking with the packaged release. We will try to provide a monthy
release, if time permits and recommend using a version of Plaso no older than
6 months.

## Roadmap

The following sections contain a rough outline of the larger items on the
roadmap. For more detailed information see:
[enhancements](https://github.com/log2timeline/plaso/labels/enhancement)

* Code clean up and optimization
  * storage
    * [storage redesign](https://github.com/log2timeline/plaso/issues/102)
    * add support for event groups
    * add support for events without a date and time value
  * analysis plugins
  * front-end, CLI, tools
  * output modules
  * text parser rewrite/optimization
* Extend and improve file system support
  * [dfVFS](https://github.com/log2timeline/dfvfs/wiki/Roadmap)
* Multi volume support
* Parsers
  * [Add more parsers](https://github.com/log2timeline/plaso/issues/518)
  * improve existing parsers
  * deprecate stat object in favour of file entry attributes
  * [Windows Registry support improvements](https://github.com/log2timeline/plaso/issues/145)
  * Handling recovered (deleted) data
* [Add more analysis plugins](https://github.com/log2timeline/plaso/issues/521)
* Hashing
  * Do NSRL matching prior to event extraction
  * Use an event database to shortcut file processing
* Deployment
  * Plaso as a module; Clean up and rewrite of the engine code (the parts that were not touched previously); Stabilize an API
  * Sandboxing the workers
  * Plaso as a service
  * Cross-system distributed Plaso workers (RPC)
