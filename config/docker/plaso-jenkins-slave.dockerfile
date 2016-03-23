# This Dockerfile is used to build an image containing basic stuff to be used as a Jenkins slave build node.
FROM ubuntu:trusty
MAINTAINER Onager <onager@deerpie.com>

# Make sure the package repository is up to date.
RUN apt-get update

# Install a basic SSH server
RUN apt-get install -y openssh-server
RUN sed -i 's|session    required     pam_loginuid.so|session    optional     pam_loginuid.so|g' /etc/pam.d/sshd
RUN mkdir -p /var/run/sshd

# Install JRE 7 (latest edition)
RUN apt-get install -y openjdk-7-jre-headless

# Install plaso bootstrapping deps
RUN apt-get install -y git python python-dev software-properties-common

# Add user jenkins to the image
RUN adduser --quiet jenkins
# Set password for the jenkins user
RUN echo "jenkins:jenkins" | chpasswd
# Add jenkins user to sudoers
RUN echo "jenkins ALL=NOPASSWD:ALL" | (EDITOR="tee -a" visudo)

# Set terminal to UTF-8 by default
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Standard SSH port
EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]