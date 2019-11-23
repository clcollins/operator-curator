"""
Module for classes representing packages and package releases.
"""

import logging
import tarfile
import requests
import yaml
from .__main__ import ALLOWED_PACKAGES, DENIED_PACKAGES, _url
from .clusterserviceversion import ClusterServiceVersion
from .validate import validate_package, validate_pacakge_release

LOGGER = logging.getLogger(__name__)


def extract_yaml_data(data):
    """
    Takes a raw stream and returns a list of files from the
    tar archive represented as tarinfo objects.
    """
    with tarfile.open(fileobj=data) as tar:
        # Should have a try/except block here, but unsure what
        # exceptions may be raised by this
        yaml_files = [
            (
                {
                    i.name: tar.extractfile(i).read()
                }
            ) for i in tar if (
                i.name.split('.')[-1:].pop() == 'yaml'
            )
        ]

    return yaml_files


def init_package_release_from_json(package, data):
    """
    Initialized PackageRelese objects from the release data list
    provided, and returns a list of PackageReleases.
    """
    release_objects = []

    for release in data:
        release_objects.append(
            PackageRelease(
                package,
                release['package'],
                release['release'],
                release['content']['digest']
            )
        )

    return release_objects


def get_release_data(name):
    """
    Queries Quay.io for a JSON list of releases associated with this
    package, and returns a list of dicts.
    """

    response = requests.get(_url(f"packages/{name}"))
    if response.ok:
        return response.json()

    return []


class Package:
    """
    Represents an Operator package.
    """

    def __init__(self, namespace, name):
        self.name = name
        self.parent_namespace = namespace
        self.namespace = self.parent_namespace.name

        logging.debug(f"Package: {self.name}")

        self.curated_name = f"curated-{self.name}"
        self.curated_namespace = f"curated-{self.namespace}"

        # Is the whole package allowed?
        self.is_in_allowed_list = self.check_package_in_allowed_list()
        logging.debug(
            f"{self.name} is_in_allowed_list: {self.is_in_allowed_list}"
        )

        # Is the whole package denied?
        self.is_in_denied_list = self.check_package_in_denied_list()
        logging.debug(
            f"{self.name} is_in_denied_list: {self.is_in_denied_list}"
        )

        self.valid, self.tests = validate_package(self)

        self.releases = []
        self.release_results = []

        # If package is valid, continue
        if self.valid:
            # Get info on curated releases, so we can skip
            # any curation attempts for already-created curated releases
            #
            # Getting and storing it here saves HTTP operations for every
            # package release.
            self.curated_release_data = get_release_data(self.curated_name)

            # Initialize package releases from the non-curated repo
            # information and test them for curation
            self.releases = init_package_release_from_json(
                self,
                get_release_data(self.name)
            )

            # Create the release summary structure for the summarization
            # at the Namespace level
            for release in self.releases:
                self.release_results.append(
                    {
                        self.name: {
                            "version": release.release,
                            "pass": release.valid,
                            "skipped": release.already_curated,
                            "tests": release.tests
                        }
                    }
                )

    def validate(self):
        """
        Runs through the list of releases, and gathers the validation
        results.
        """

    def check_package_in_allowed_list(self):
        """
        Returns true of the package has been listed in the allow list.
        """
        if self.name in ALLOWED_PACKAGES:
            return True

        return False

    def check_package_in_denied_list(self):
        """
        Returns true of the package has been listed in the deny list.
        """
        if self.name in DENIED_PACKAGES:
            return True

        return False


class PackageRelease:
    """
    Represents a specific version of an operator package.
    """

    def __init__(self, package, name, release, digest):
        self.package = package

        self.name = name
        self.digest = digest
        self.release = release

        logging.debug(f"PackageRelease: {name} - {release}")

        self.digest_url = _url(
            f"packages/{self.name}/blobs/sha256/{self.digest}"
        )

        self.upload_url = _url(
            f"packages/{self.package.curated_name}"
        )

        self.already_curated = self.check_if_already_curated()

        namestring = f"{self.name} - {self.release}"
        logging.debug(
            f"{namestring} already_curated: {self.already_curated}"
        )

        if self.already_curated:
            self.csvs = []
            self.contents = ''

            # TODO: Implement this in the report
            # ...
            #   [SKIP] self.name - self.release
            #       [SKIP] release has already been curated

        else:
            # Only need to get the data if PackageRelease is
            # not curated yet
            self.contents = extract_yaml_data(
                self.download_release()
            )

            self.csvs = self.init_csvs_from_contents()

        self.valid, self.tests = validate_pacakge_release(self)
        if self.valid:
            self.upload_release()

    def check_if_already_curated(self):
        """
        Checks the curation data for the parent package to see if this
        PackageRelease has already been curated.

        Returns a boolean = True if curated, False if not.
        """

        curated = [
            i for i in (
                self.package.curated_release_data
            ) if self.release in i.values()
        ]

        logging.debug(f"Matched curated release data: {curated}")

        return bool(curated)

    def download_release(self):
        """
        Downloads the release tarball for the specified digest, and
        returns the raw result for extraction.
        """

        logging.debug(
            f"Downloading {self.name} - {self.release}"
            f" from {self.digest_url}"
        )
        response = requests.get(self.digest_url, stream=True)

        # Return the raw response object
        if response.ok:
            return response.raw

        return None

    def upload_release(self):
        """
        Uploads the release to the curated namespace.
        """
        logging.info(
            f"Uploading {self.name} - {self.release} to"
            f"{self.package.curated_namespace}"
        )

        return True
#        with open(self.contents, 'r') as f:
#          encoded_bundle = base64.b64encode(f.read())
#          encoded_bundle_str = encoded_bundle.decode()
#
#        # IS MEDIA TYPE ALWAYS HELM?
#        payload = {
#          "blob": encoded_bundle_str,
#          "release": self.release,
#          "media_type": "helm"
#        }
#
#        try:
#            response = requests.post(
#                self.upload_url,
#                data=json.dumps(payload),
#                headers=_quay_headers(basic_token)
#            )
#            response.raise_for_status()
#        except requests.exceptions.HTTPError as error:
#            if response.status_code == 409:
#                #logging.info(
#                   f"Version {version} of {shortname} is already present"
#                   f" in {target_namespace} namespace. Skipping..."
#                 )
#                # HOW TO LOGGING
#                pass
#            else:
#                #logging.error(
#                   f"Failed to upload {shortname} to "
#                   f"{target_namespace} namespace. HTTP Error: {error}"
#                 )
#                pass
#        except requests.exceptions.ConnectionError as error:
#                #logging.error(
#                   f"Failed to upload {shortname} to "
#                   f"{target_namespace} namespace. Connection Error: {error}"
#                 )
#            pass
#        except requests.exceptions.Timeout as error:
#                #logging.error(
#                   f"Failed to upload {shortname} to "
#                   f"{target_namespace} namespace. Timeout Error: {error}"
#                 )
#            pass
#
#        # This is a new package namespace, make it publicly visible
#        set_repo_visibility(target_namespace, shortname, oauth_token)

    def init_csvs_from_contents(self):
        """
        Takes a list of tarinfo files, and searches for
        clusterServiceVersions in them.
        """
        csv_list = []
        for entry in self.contents:
            for _, value in entry.items():
                item = yaml.safe_load(value)
                if 'kind' in item.keys():
                    if item['kind'] == 'ClusterServiceVersion':
                        # This is a csv
                        csv_list.append(ClusterServiceVersion(item))
                if 'channels' in item.keys():
                    # This is a package manifest
                    self.package_manifest = item

                if 'data' in item.keys():
                    # This is a bundle
                    if 'clusterServiceVersions' in item['data']:
                        csv_specs = yaml.safe_load(
                            item['data']['clusterServiceVersions']
                        )
                        self.package_manifest = yaml.safe_load(
                            item['data']['packages']
                        )
                        for csv in csv_specs:
                            csv_list.append(ClusterServiceVersion(csv))

        return csv_list
