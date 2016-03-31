FROM ubuntu:15.10
MAINTAINER Michal Wrona <"michal.wrona.4@gmail.com">

# Get the image up to date
RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get clean

# Install basic packages
RUN apt-get install -y curl python python-setuptools python-rados && \
    apt-get clean

# Install luma dependencies
RUN easy_install Flask Flask-SQLAlchemy

ADD luma.tar /root/luma
ADD run_luma.sh /root/luma

# Add default configurations
ADD config.cfg /root/luma
ADD generators_mapping.json /root/luma
ADD generators.cfg /root/luma/generators

EXPOSE 5000

CMD /root/luma/run_luma.sh
