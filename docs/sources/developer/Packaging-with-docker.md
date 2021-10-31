## Packaging with Docker

To create a Docker packaged release from the development release you also need:

* Docker

### Packaging

Build Plaso Docker image:

```
./utils/build_docker.sh
```

This will create a local Docker image: log2timeline/plaso:latest

