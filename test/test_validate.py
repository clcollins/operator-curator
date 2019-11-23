"""
Contains unit tests for the validate module.
"""

import unittest
from unittest.mock import patch
from operatorcurator import clusterserviceversion as csv
from operatorcurator import package as pkg
from operatorcurator import validate


class TestValidateCSV(unittest.TestCase):
    """
    Contains unit tests for the validate module.
    """

    def test_validate_csv_pass(self):
        """
        Tests the validate_csv function.
        """

        with patch.object(csv.ClusterServiceVersion,
                          "__init__",
                          lambda x, y: None):

            mock_csv = csv.ClusterServiceVersion('some_yaml')
            mock_csv.requires_cluster_permissions = False
            mock_csv.requires_security_context_constraints = False
            mock_csv.allows_multinamespace_install_mode = False

            expected = {
                'requires clusterPermissions': False,
                'requires securityContextConstraints': False,
                'allows multiNamespace installMode': False
            }

            valid, tests = validate.validate_csv(mock_csv)

            self.assertTrue(valid)
            self.assertDictEqual(expected, tests)

    def test_validate_csv_fail(self):
        """
        Test different permuations of the validate_csv function with
        expected vailing results.
        """

        with patch.object(csv.ClusterServiceVersion,
                          "__init__",
                          lambda x, y: None):

            mock_csv = csv.ClusterServiceVersion('some_yaml')
            mock_csv.requires_cluster_permissions = True
            mock_csv.requires_security_context_constraints = False
            mock_csv.allows_multinamespace_install_mode = False

            expected = {
                'requires clusterPermissions': True,
                'requires securityContextConstraints': False,
                'allows multiNamespace installMode': False
            }

            valid, tests = validate.validate_csv(mock_csv)

            self.assertFalse(valid)
            self.assertDictEqual(expected, tests)

        with patch.object(csv.ClusterServiceVersion,
                          "__init__",
                          lambda x, y: None):

            mock_csv = csv.ClusterServiceVersion('some_yaml')
            mock_csv.requires_cluster_permissions = False
            mock_csv.requires_security_context_constraints = True
            mock_csv.allows_multinamespace_install_mode = False

            expected = {
                'requires clusterPermissions': False,
                'requires securityContextConstraints': True,
                'allows multiNamespace installMode': False
            }

            valid, tests = validate.validate_csv(mock_csv)

            self.assertFalse(valid)
            self.assertDictEqual(expected, tests)

        with patch.object(csv.ClusterServiceVersion,
                          "__init__",
                          lambda x, y: None):

            mock_csv = csv.ClusterServiceVersion('some_yaml')
            mock_csv.requires_cluster_permissions = False
            mock_csv.requires_security_context_constraints = False
            mock_csv.allows_multinamespace_install_mode = True

            expected = {
                'requires clusterPermissions': False,
                'requires securityContextConstraints': False,
                'allows multiNamespace installMode': True
            }

            valid, tests = validate.validate_csv(mock_csv)

            self.assertFalse(valid)
            self.assertDictEqual(expected, tests)

        with patch.object(csv.ClusterServiceVersion,
                          "__init__",
                          lambda x, y: None):

            mock_csv = csv.ClusterServiceVersion('some_yaml')
            mock_csv.requires_cluster_permissions = True
            mock_csv.requires_security_context_constraints = False
            mock_csv.allows_multinamespace_install_mode = True

            expected = {
                'requires clusterPermissions': True,
                'requires securityContextConstraints': False,
                'allows multiNamespace installMode': True
            }

            valid, tests = validate.validate_csv(mock_csv)

            self.assertFalse(valid)
            self.assertDictEqual(expected, tests)


class TestValidatePackage(unittest.TestCase):
    """
    Contains unit tests for validate.validate_package module.
    """

    def test_validate_pkg_pass(self):
        """
        Tests the validate_pkg function.
        """

        with patch.object(pkg.Package,
                          "__init__",
                          lambda x, y, z: None):
            mock_pkg = pkg.Package('namespace', 'name')
            mock_pkg.is_in_denied_list = False
            mock_pkg.is_in_allowed_list = False

            expected = {
                'package is in denied list': False,
                'package is in allowed list': False
            }

            valid, tests = validate.validate_package(mock_pkg)

            self.assertTrue(valid)
            self.assertDictEqual(expected, tests)

        with patch.object(pkg.Package,
                          "__init__",
                          lambda x, y, z: None):
            mock_pkg = pkg.Package('namespace', 'name')
            mock_pkg.is_in_denied_list = False
            mock_pkg.is_in_allowed_list = True

            expected = {
                'package is in denied list': False,
                'package is in allowed list': True
            }

            valid, tests = validate.validate_package(mock_pkg)

            self.assertTrue(valid)
            self.assertDictEqual(expected, tests)

    def test_validate_pkg_fail(self):
        """
        Tests the validate_pkg function.
        """

        with patch.object(pkg.Package,
                          "__init__",
                          lambda x, y, z: None):
            mock_pkg = pkg.Package('namespace', 'name')
            mock_pkg.is_in_denied_list = True
            mock_pkg.is_in_allowed_list = False

            expected = {
                'package is in denied list': True,
                'package is in allowed list': False
            }

            valid, tests = validate.validate_package(mock_pkg)

            self.assertFalse(valid)
            self.assertDictEqual(expected, tests)

        with patch.object(pkg.Package,
                          "__init__",
                          lambda x, y, z: None):
            mock_pkg = pkg.Package('namespace', 'name')
            mock_pkg.is_in_denied_list = True
            mock_pkg.is_in_allowed_list = True

            expected = {
                'package is in denied list': True,
                'package is in allowed list': True
            }

            valid, tests = validate.validate_package(mock_pkg)

            self.assertFalse(valid)
            self.assertDictEqual(expected, tests)


class TestValidatePackageRelease(unittest.TestCase):
    """
    Contains unit tests for validate.validate_package_release.
    """

    def test_validate_package_release_pass_if_curated(self):
        """
        Tests passing results from the validate_package_release function,
        specifically that it auto-passes if already curated.
        """

        with patch.object(pkg.PackageRelease,
                          "__init__",
                          lambda v, w, x, y, z: None):
            mock_release = pkg.PackageRelease(
                'package',
                'name',
                'release',
                'digest'
            )

            mock_release.already_curated = True

            expected = {
                'release has already been curated': True
            }

            valid, tests = validate.validate_pacakge_release(mock_release)

            self.assertTrue(valid)
            self.assertDictEqual(expected, tests)

    def test_validate_package_release_pass(self):
        """
        Tests all other passing results from the
        validate_package_release function.
        """

        with patch.object(pkg.PackageRelease,
                          "__init__",
                          lambda v, w, x, y, z: None):
            mock_release = pkg.PackageRelease(
                'package',
                'name',
                'release',
                'digest'
            )

            mock_release.already_curated = False

#            expected = {
#                'release has already been curated': True
#            }
#
#            valid, tests = validate.validate_pacakge_release(mock_release)
#
#            self.assertTrue(valid)
#            self.assertDictEqual(expected, tests)

    def test_validate_package_release_fail(self):
        """
        Tests failing results from the validate_package_release function.
        """

        with patch.object(pkg.PackageRelease,
                          "__init__",
                          lambda v, w, x, y, z: None):
            mock_release = pkg.PackageRelease(
                'package',
                'name',
                'release',
                'digest'
            )

            mock_release.already_curated = False

#            expected = {
#                'release has already been curated': False
#            }
#
#            valid, tests = validate.validate_pacakge_release(mock_release)
#
#            self.assertTrue(valid)
#            self.assertDictEqual(expected, tests)
