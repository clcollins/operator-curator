"""
Test cases for classes in the packages module.
"""

import unittest
from unittest.mock import patch

import yaml
from operatorcurator import package, namespace


class TestPackages(unittest.TestCase):
    """
    Contains test for the Package class.
    """

    def get_test_yaml(self, yaml_file):
        """
        Open and retrieve some yaml from the test data to use for
        these tests.
        """

        with open(yaml_file, 'r') as yaml_data:
            test_yaml = yaml.safe_load(yaml_data)

        return test_yaml

    def test_extract_yaml_data(self):
        """
        Tests extraction of yaml data from tar file.
        """

        with open('test/data/example_bundle_tarball.tgz', 'rb') as data:
            yaml_files = package.extract_yaml_data(data)

        # just validate it parses
        self.assertTrue(
            yaml.safe_load(
                yaml_files[0]['bundle.1.0.0.yaml']
            )
        )

        with open('test/data/example_csvlist_tarball.tgz', 'rb') as data:
            yaml_files = package.extract_yaml_data(data)

        name = (
            f"codeready-workspaces-vdkrqant/"
            f"codeready-workspaces.package.yaml"
        )

        # just validate it parses
        self.assertTrue(
            yaml.safe_load(
                yaml_files[0][name]
            )
        )

    # TODO: Figure out why this isn't working
    def test_init_csvs_from_contents(self):
        """
        Tests loading a list of csvs from a list of {name:data} dicts.
        """

#        with open('test/data/example_bundle_tarball.tgz', 'rb') as data:
#            yaml_files = package.extract_yaml_data(data)
#
#        csvs = package.init_csvs_from_contents(yaml_files)
#
#        self.assertEqual(csvs[0].name, "amqstreams.v1.0.0")
#        self.assertEqual(csvs[0].version, '1.0.0')
#
#
#        with open('test/data/example_csvlist_tarball.tgz', 'rb') as data:
#            yaml_files = package.extract_yaml_data(data)
#
#        csvs = package.init_csvs_from_contents(yaml_files)
#
#        self.assertEqual(csvs[0].name, "crwoperator.v1.2.0")
#        self.assertEqual(csvs[0].version, '1.2.0')
#
#        # This is the right data, but it's GOT to be a mistake in the
#        # csv for the operator.
#        self.assertEqual(csvs[1].name, "crwoperator.v1.2.2")
#        self.assertEqual(csvs[1].version, '1.2.0')

    def test_package_release_init(self):
        """
        Tests the initialization of a PackageRelease object.
        """

        # TODO:  Needs mock for download_release

        # Example testing with live Quay.io request:
        #
        # with open('test/data/example_quay_package_data.json', 'r') as data:
        #     package_data = json.load(data)

        # release = package_data[4]
        # pkg = package.PackageRelease(
        #     release['package'],
        #     release['release'],
        #     release['content']['digest']
        # )

        # self.assertEqual(pkg.csvs[0].name, 'crwoperator.v1.2.0')
        # self.assertFalse(pkg.csvs[0].requires_cluster_permissions)

    def test_package_release_download_release(self):
        """
        Tests the response from the function downloading the package
        data from Quay.io.
        """

        # TODO: Needs mock for requests

    def test_check_package_in_allowed_list(self):
        """
        Tests that the function returns True if the operator package is
        in the ALLOWED_PACKAGES list.
        """

        # TODO

    def test_check_package_in_denied_list(self):
        """
        Tests that the function returns True if the operator package is
        in the DENIED_PACKAGES list.
        """

        # TODO

    def test_package_init(self):
        """
        Tests initialization of the package object.
        """
        with patch.object(
                namespace.Namespace,
                "__init__",
                lambda w, x, y: None
        ):
            mock_namespace = namespace.Namespace(
                'redhat-operators',
                []
            )
            mock_namespace.name = 'redhat-operators'

            pkg = package.Package(
                mock_namespace,
                "redhat-operators/codeready-workspaces"
            )

            self.assertEqual(pkg.name, "redhat-operators/codeready-workspaces")
            self.assertEqual(pkg.namespace, "redhat-operators")
            self.assertEqual(pkg.curated_namespace, "curated-redhat-operators")

            # TODO: These should have a mocked list, and not depend on
            # the lists in main

            self.assertTrue(pkg.is_in_allowed_list)
            self.assertFalse(pkg.is_in_denied_list)

    def test_init_package_release_from_json(self):
        """
        Tests that a list of PackageReleases are returned when
        JSON data containing release information from Quay.io is
        provided.
        """

        # TODO: Need to mock requests in PackageReleases class
        # pass.  This is how you would do it live:

        # with open('test/data/example_quay_package_data.json', 'r') as data:
        #     release_list = package.init_package_release_from_json(
        #         json.load(data))

        # This is a dumb test - just an example placeholder
        # self.assertTrue(release_list)

    def test_get_release_data(self):
        """
        Tests function responds with JSON data containing the release
        information for the operator package.
        """

        # TODO: Needs mock for requests
