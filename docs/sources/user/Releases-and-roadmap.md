Plaso comes in 2 different forms of releases:

* a packaged release; found on the [releases page](https://github.com/log2timeline/plaso/releases)
* a development release; found in the [git repository](https://github.com/log2timeline/plaso)

**Note that the development release is for development, expect frequent updates and potential breakage.**

If you do not plan to develop or live on the edge, regarding plaso, we highly recommend sticking with the packaged release. We will try to provide two packaged releases per year, a "summer" and "winter" release (depending on your location), but occasionally we will also do preview and release candidate packaged releases.

## Roadmap
The following sections contain a rough outline of the larger items on the roadmap. For more detailed information see: [enhancements](https://github.com/log2timeline/plaso/labels/enhancement)

* [Artifact support](https://github.com/log2timeline/plaso/issues/155)
* Refactors
  * storage
    * redesign how event objects are stored
    * add support for event groups
    * add support for events without a date and time value
  * analysis plugins
  * front-end, CLI, tools
  * output modules
  * text parser rewrite/optimization
* Improve file system support
  * [dfVFS](https://github.com/log2timeline/dfvfs/wiki/Roadmap)
* Multi volume support
* [Add Python 3 support](https://github.com/log2timeline/plaso/issues/511)
* Parsers
  * improve existing parsers
    * job file parser - add format improvements
  * deprecate stat object in favour of file entry attributes
* [Add more parsers](https://github.com/log2timeline/plaso/issues/518)
* [Add more analysis plugins](https://github.com/log2timeline/plaso/issues/521)
* Collection
  * Improve collection filters
* Hashing
  * Do NSRL matching prior to event extraction
  * Use an event database to shortcut file processing
* Deployment
  * Plaso as a module; Clean up and rewrite of the engine code (the parts that were not touched previously); Stabilize an API
  * Sandboxing the workers
  * Plaso as a service
  * Cross-system distributed plaso workers (RPC)
  * [storage redesign](https://github.com/log2timeline/plaso/issues/102)
* [Windows Registry support improvements](https://github.com/log2timeline/plaso/issues/145)
* Handling recovered (deleted) data
