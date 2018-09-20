# Plaso in a Docker container

## Install Docker on Ubuntu
`apt-get install docker.io`
## Build an image 
### From Docker Public Registry
`$ docker pull log2timeline/plaso`
### From Dockerfile
```
$ git clone https://github.com/log2timeline/plaso
$ cd log2timeline/plaso/config/docker/
$  docker build -f plaso-from-ppa.dockerfile .
```
## Export the Plaso docker image to a non-internet connected system
Figure out the name of the docker image you want to run, using the IMAGE ID (docker images will list all the images you have installed) if you've built from the Dockerfile. Use "log2timeline/plaso" if you've just made the image from the Docker Registry

First, export the image:
`$ docker save <CONTAINER_NAME> | gzip -c > saved_docker_image.tgz`

Then copy saved_docker_image.tgz to an external disk.

Finally, on the other system, and from the mounted external disk, run:

`$ zcat saved_docker_image.tgz | docker load`

## Run Plaso from your new docker image
Figure out the name of the docker image you want to run (see before)

First start the extraction with log2timeline. Should your evidence files/images should be present on the host, and not in the container (which is the default scenario), you'll have to set up a bridge between the two.
For example, if you store your current evidences to analyse in /data/evidences/,  you could tell log2timeline to generate the plaso storage file as /data/evidences.plaso this way:
```$ docker run -v /data/:/data log2timeline/plaso log2timeline /data/evidences.plaso /data/evidences``

This way your plaso file will also be stored on the host filesystem.

Next step is to run analysis with psort:
```
$ docker run -v /data/:/data log2timeline/plaso psort /data/evidences.plaso 
Datetime,timestamp_desc,source,source_long,message,parser,display_name,tag,store_number,store_index
....
Processing completed.

*********************************** Counter ************************************
     Stored Events : 251
   Events Included : 251
Duplicate Removals : 23
--------------------------------------------------------------------------------
```

Last step, forensication, is left to the reader. 

The entry_point of the docker container is [plaso-swtch.sh](https://github.com/log2timeline/plaso/blob/master/config/docker/plaso-switch.sh). It understands the following commands, and runs the appropriate programs:
log2timeline or log2timeline.py
pinfo or pinfo.py
preg  or preg.py
psort or psort.py


If you're not interested in running any of these, and just want to drop to a prompt inside your Plaso container, you can run:
`docker run -t -i --entrypoint=/bin/bash -v /data:/data log2timeline.plaso `