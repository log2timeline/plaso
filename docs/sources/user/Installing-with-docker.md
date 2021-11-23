# Plaso in a Docker container

## Install Docker

To install Docker see: [https://docs.docker.com/get-docker](https://docs.docker.com/get-docker)

## Obtaining a Plaso Docker image

### From Docker Hub

```bash
$ docker pull log2timeline/plaso
```

### From Dockerfile

```bash
$ git clone https://github.com/log2timeline/plaso
$ cd plaso/config/docker
$ docker build -f Dockerfile .
```

### Testing your Plaso Docker image

To test your Plaso Docker image:

```bash
$ docker run log2timeline/plaso log2timeline.py --version
plaso - log2timeline version 20200717
```

## Copying the Plaso Docker image to a non-Internet connected system

Figure out the name of the Docker image you want to run, using the IMAGE ID
(Docker images will list all the images you have installed) if you've built
from the Dockerfile. Use "log2timeline/plaso" if you've just made the image
from Docker Hub.

First, export the image:

```bash
$ docker save <CONTAINER_NAME> | gzip -c > saved_docker_image.tgz
```

Then copy saved_docker_image.tgz to an external disk.

Finally, on the other system, and from the mounted external disk, run:

```bash
$ zcat saved_docker_image.tgz | docker load
```

## Run Plaso from your new Docker image

Figure out the name of the Docker image you want to run (see before)

First start the extraction with log2timeline. Should your evidence files/images
should be present on the host, and not in the container (which is the default
scenario), you'll have to set up a bridge between the two.
For example, if you store your current evidences to analyse in
/data/evidences/, you could tell log2timeline to generate the Plaso storage
file as /data/evidences.plaso this way:

```bash
$ docker run -v /data/:/data log2timeline/plaso log2timeline --storage-file /data/evidences.plaso /data/evidences
```

This way your Plaso file will also be stored on the host filesystem.

Note that if you are running SELinux you likely need to add the `:z` volume
flag. Also see: [Configure the selinux label](https://docs.docker.com/storage/bind-mounts/#configure-the-selinux-label).

Note that if you are running Windows adding a "Mapped Network Drive" might not
work with WSL. Also see: [Mapped drives as shared drives with linux containers: This shared resource does not exist. #2163](https://github.com/docker/for-win/issues/2163).

Next step is to run analysis with psort:

```bash
$ docker run -v /data/:/data log2timeline/plaso psort -w /data/timeline.log /data/evidences.plaso
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

The entry_point of the Docker container is [plaso-switch.sh](https://github.com/log2timeline/plaso/blob/main/config/docker/plaso-switch.sh).
It understands the following commands, and runs the appropriate programs:

* log2timeline or log2timeline.py
* pinfo or pinfo.py
* psort or psort.py
* psteal  or psteal.py

If you're not interested in running any of these, and just want to drop to a
prompt inside your Plaso container, you can run:

```bash
docker run -t -i --entrypoint=/bin/bash -v /data:/data log2timeline/plaso
```
