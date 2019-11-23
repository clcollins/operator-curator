FROM registry.access.redhat.com/ubi8/ubi-minimal
LABEL maintainer "Red Hat OpenShift Dedicated SRE Team"

RUN microdnf install -y python3 python3-pip make git
RUN python3 -m pip install pyyaml requests

COPY . ./

RUN make test
RUN python3 -m pip install .

ENTRYPOINT ["operator-curator"]
CMD ["--help"]

