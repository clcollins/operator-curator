import sys

SOURCE_NAMESPACES = [
    "redhat-operators",
#    "certified-operators",
#    "community-operators"
]

ALLOWED_PACKAGES = [
    "redhat-operators/cluster-logging",
    "redhat-operators/elasticsearch-operator",
    "redhat-operators/codeready-workspaces"
]

DENIED_PACKAGES = [
    "certified-operators/mongodb-enterprise",
    "community-operators/etcd",
    "community-operators/federation",
    "community-operators/syndesis"
]

def _url(path):
    """
    Accepts a path string and returns the full URL for the
    Quay.io cnr API.
    """
    return "https://quay.io/cnr/api/v1/" + path

