FROM python:3.7.2-stretch
RUN apt-get install -y ca-certificates openssl \
&& wget https://storage.googleapis.com/kubernetes-release/release/v1.13.0/bin/linux/amd64/kubectl -O /usr/local/bin/kubectl \
&& chmod a+x /usr/local/bin/kubectl /usr/local/bin/dumb-init \
&& apk --no-cache del ca-certificates openssl \
&& pip install pyyaml \
&& mkdir /deploy

ADD . /bin/
RUN chmod a+x /bin/deploy
WORKDIR /root/
CMD ["bash"]