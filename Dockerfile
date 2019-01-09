FROM python:3.7.2-stretch
RUN apt-get install -y gettext ca-certificates openssl \
&& wget https://github.com/Yelp/dumb-init/releases/download/v1.2.0/dumb-init_1.2.0_amd64 -O /usr/local/bin/dumb-init \
&& wget https://storage.googleapis.com/kubernetes-release/release/v1.13.0/bin/linux/amd64/kubectl -O /usr/local/bin/kubectl \
&& chmod a+x /usr/local/bin/kubectl /usr/local/bin/dumb-init \
&& apk --no-cache del ca-certificates openssl \
&& pip install pyyaml \
&& mkdir /deploy

ADD . /bin/
RUN chmod +x /bin/deploy
WORKDIR /root/
ENTRYPOINT ["/usr/local/bin/dumb-init","--","/usr/local/bin/docker-entrypoint.sh"]
CMD ["bash"]