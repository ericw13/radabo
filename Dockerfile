FROM centos:latest
MAINTAINER Eric Wright <ewright@redhat.com>

RUN yum update -y

# Install the necesary Python stuff
RUN yum install -y epel-release

RUN yum install -y python-devel python-pip
RUN pip install --upgrade pip

# Install necesary libraries
RUN yum install -y mariadb-devel gcc
RUN yum install -y httpd mod_wsgi patch
# For diagnostics
RUN yum install -y net-tools
RUN yum install -y iproute

RUN mkdir /opt/radabo && mkdir /opt/radabo/app && mkdir /opt/radabo/static_serv
RUN chown -R apache:apache /opt/radabo
RUN yum clean all -y

# Add and install pip requirements first so that we don't have to do it each time files are changed in the main app
ADD app/requirements.txt /opt/radabo/
RUN pip install -r /opt/radabo/requirements.txt

# Add application files
ADD docker/conf/radabo_apache.conf /etc/httpd/conf.d/

ADD docker/conf/run.sh /opt/radabo/
ADD app/ /opt/radabo/app
# The Pinger class does not work in containers and should be removed
# cf. https://github.com/RallyTools/RallyRestToolkitForPython/pull/64
ADD docker/conf/context.patch /opt/radabo/app

RUN patch /usr/lib/python2.7/site-packages/pyral/context.py /opt/radabo/app/context.patch

RUN echo yes | python /opt/radabo/app/manage.py collectstatic

EXPOSE 80 443
CMD ["/opt/radabo/run.sh"]
