"""
Classes and functions for channel objects
"""

import logging
from .validate import validate_channel

LOGGER = logging.getLogger(__name__)


def retrieve_csv_by_name(desired_csv_name, csv_list):
    """
    Retrieve a csv object from the parent package release.
    """
    for csv in csv_list:
        if csv.name == desired_csv_name:
            return csv

    return None


class Channel():
    """
    Represents a channel from the package manifest.
    """

    def __init__(self, package_release, channel_yaml):
        """
        Initialize the object.
        """
        self.package_release = package_release

        self.yaml = channel_yaml
        self.name = self.yaml['name']
        self.current_csv_name = self.yaml['currentCSV']
        self.current_csv_valid = False

        logging.debug(f"Channel: {self.name}")
        logging.debug(f"Channel currentCSV: {self.current_csv_name}")

        self.valid = False
        self.tests = {}

    def repackage_and_validate(self):
        """
        Repackage the channel with only valid CSVs
        """

        valid_csvs = []

        current_csv = retrieve_csv_by_name(
            self.current_csv_name,
            self.package_release.csvs
        )

        if current_csv is None:
            print(self.current_csv_name)
            print(len(self.package_release.csvs))
            raise RuntimeError("CURRENT CSV IS NONE")

        if current_csv.valid:
            valid_csvs.append(current_csv)
            logging.debug(f"currentCSV is valid")
            self.current_csv_valid = True

        self.valid, self.tests = validate_channel(self)
