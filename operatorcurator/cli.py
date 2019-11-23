import sys
import argparse
import logging
from .__main__ import SOURCE_NAMESPACES
from .namespace import Namespace
from .summary import Summary

logger = logging.getLogger(__name__)

def main():
    """
    Parses command line arguments.
    """
    parser = argparse.ArgumentParser(
        description=("""A tool for curating application registry for
            use with OSDv4."""))
    parser.add_argument(
        '--app-token', action="store",
        dest="basic_token", type=str,
        help="Basic auth token for use with Quay's CNR API")
    parser.add_argument(
        '--oauth-token', action="store",
        dest="oauth_token", type=str,
        help="Oauth token for use with Quay's repository API")
    # No longer storing data on the filesystem
    # parser.add_argument(
    #    '--cache', action="store_true",
    #    default=False, dest="use_cache",
    #    help="Use local cache of operator packages")
    parser.add_argument(
        '--skip-push', action="store_true",
        default=False, dest="skip_push",
        help="Skip pushing validated packages to Quay.io")
    parser.add_argument(
        '--log-level', action="store",
        default='info', dest="log_level", type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="Set verbosity of logs printed to STDOUT.")

    args = parser.parse_args()

    import logging.config
    loglevel= getattr(logging, args.log_level.upper(), None)
    logging.basicConfig(level=loglevel)

    summary = Summary()

    for name in SOURCE_NAMESPACES:
        Namespace(name, summary)

    summary.summarize()