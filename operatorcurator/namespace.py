"""
This module creates Namespace objects as the top-level object in the
curation process.
"""

import logging
import requests
from .__main__ import _url
from .package import Package

LOGGER = logging.getLogger(__name__)


def list_operators(self):
    """
    Accepts a namespace and returns
    a list of operators in the namespace.
    """
    response = requests.get(self.operators_url)
    if response.ok:
        operator_list = [
            str(item['name']) for item in response.json()
        ]
        return operator_list

    logging.debug(f"No operators found for {self.name}")
    return None


class Namespace:
    """
    Represents a Quay.io application registry namespace.
    """

    def __init__(self, name, summary):
        self.name = name

        self.operators_url = _url(f"packages?namespace={self.name}")
        self.operators = list_operators(self)

        logging.debug(f"Namespace: {self.name}")

        # For operator in list:
        for package in self.operators:
            logging.debug(package)
            pkg = Package(self, package)

            valid, tests = pkg.valid, pkg.tests

            if valid:
                release_results = pkg.release_results
                for result in release_results:
                    summary.report.append(result)
            else:
                summary.report.append(
                    {
                        self.name: {
                            "version": "all versions",
                            "pass": False,
                            "skipped": False,
                            "tests": tests
                        }
                    }
                )

            # Delete the packge object when we're done, to save memory
            del pkg
