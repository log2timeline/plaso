# This Dockerfile is used to build an image containing components to be
# used as a Jenkins slave build node.
FROM ubuntu:trusty
MAINTAINER Log2Timeline <log2timeline-dev@googlegroups.com>

ENV JENKINS_REMOTING_VERSION 2.52
ENV HOME /home/jenkins

# Make sure the package repository is up to date.
RUN apt-get update && apt-get install -y openjdk-7-jre-headless git \
  python python-dev software-properties-common curl

# Add user jenkins to the image
RUN useradd -c "Jenkins user" -d $HOME -m jenkins
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

RUN curl --create-dirs -sSLo \
  /usr/share/jenkins/remoting-$JENKINS_REMOTING_VERSION.jar \
  https://repo.jenkins-ci.org/public/org/jenkins-ci/main/remoting/$JENKINS_REMOTING_VERSION/remoting-$JENKINS_REMOTING_VERSION.jar \
  && chmod 755 /usr/share/jenkins

COPY jenkins-slave /usr/local/bin/jenkins-slave.sh

USER jenkins

VOLUME /home/jenkins

ENTRYPOINT ["/usr/local/bin/jenkins-slave.sh"]