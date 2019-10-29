import unittest
import curator
from io import StringIO
import requests
from unittest.mock import Mock, patch


class TestStringFormattingHelpers(unittest.TestCase):
    def test_url(self):
        self.assertEqual(curator._url("some/url/path"),
                         "https://quay.io/cnr/api/v1/some/url/path")


    def test_repo_url(self):
        self.assertEqual(curator._repo_url("some/url/path"),
                         "https://quay.io/api/v1/some/url/path")


    def test_quay_headers(self):
         self.assertEqual(curator._quay_headers("someAuthToken"),
            {'Authorization': 'someAuthToken', 'Content-Type': 'application/json'}
        )

    def test_pkg_shortname(self):
        self.assertEqual(curator._pkg_shortname("some-namespace/some-package"),
                         "some-package")


@patch('curator.requests.get')
class TestRequests(unittest.TestCase):
    def test_list_operators(self, mock_get):
        expected = ['redhat-operators/nfd', 'redhat-operators/metering-ocp']
        json_response = [{'channels': None, 'created_at': '2019-10-16T20:37:35', 'default': '1.0.0', 'manifests': ['helm'], 'name': 'redhat-operators/nfd', 'namespace': 'redhat-operators', 'releases': ['1.0.0'], 'updated_at': '2019-10-16T20:37:35', 'visibility': 'public'}, {'channels': None, 'created_at': '2019-10-16T20:37:49', 'default': '1.0.0', 'manifests': ['helm'], 'name': 'redhat-operators/metering-ocp', 'namespace': 'redhat-operators', 'releases': ['1.0.0'], 'updated_at': '2019-10-16T20:37:49', 'visibility': 'public'}]
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = json_response

        response = curator.list_operators("redhat-operators")

        self.assertListEqual(response, expected)


    def test_get_release_data(self, mock_get):
        expected =  {'1.0.0': '95b49e2966a8f941d6608bb1ff95ec0e17bdfebcb46a844e7f0205f2972d2824'}
        json_response = [{'content': {'digest': '95b49e2966a8f941d6608bb1ff95ec0e17bdfebcb46a844e7f0205f2972d2824', 'mediaType': 'application/vnd.cnr.package.helm.v0.tar+gzip', 'size': 13140, 'urls': []}, 'created_at': '2019-10-16T20:37:35', 'digest': 'sha256:8a752a4887c42d4d1f7059d3a510db2a3f900325ced7b4cbb7a77d0fbf7cbfda', 'mediaType': 'application/vnd.cnr.package-manifest.helm.v0.json', 'metadata': None, 'package': 'redhat-operators/nfd', 'release': '1.0.0'}]
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = json_response

        response = curator.get_release_data('nfd')

        self.assertDictEqual(response, expected)


    # Not sure how to test this
    # def test_retrieve_package(self, mock_get):


@patch('curator.ALLOWED_PACKAGES',
    ["wonka-industries/gobstopper-firmware",
     "stark-industries/jarvis"]
)
@patch('curator.DENIED_PACKAGES',
    ["skynet/find-john-connor",
     "spacely-sprockets/red-button-input"]
)
class TestBundleValidation(unittest.TestCase):
    # The validate_bundle function need to be WAY shorter and more specific!
    # Break it up into smaller pieces!
    # def test_validate_bundle(self):

    def test_check_package_in_allow_list_true(self):
        package = "stark-industries/jarvis"
        name, result = curator.check_package_in_allow_list(package)

        self.assertEqual(name, 'is in allowed list')
        self.assertTrue(result)


    def test_check_package_in_allow_list_false(self):
        package = "skynet/find-john-connor"
        name, result = curator.check_package_in_allow_list(package)

        self.assertEqual(name, 'is in allowed list')
        self.assertFalse(result)


    def test_check_package_in_deny_list_true(self):
        package = "skynet/find-john-connor"
        name, result = curator.check_package_in_deny_list(package)

        self.assertEqual(name, 'is in denied list')
        self.assertTrue(result)


    def test_check_package_in_deny_list_false(self):
        package = "start-industries/jarvis"
        name, result = curator.check_package_in_deny_list(package)

        self.assertEqual(name, 'is in denied list')
        self.assertFalse(result)

    # Not sure how to test this
    # def extract_bundle_from_tar_file(self):

    # Not sure how to test this
    # Input is an io.BufferedReader object from the tarfile.extractfile()
    # def load_yaml_from_bundle_object

#    def test_get_packages_from_bundle_true(self):
#        bundle_yaml = ""
#        packages, name, result = curator.get_packages_from_bundle(bundle_yaml)
#
#        self.assertIsNotNone(packages)
#        self.assertEqual(name, 'bundle must have a package object')
#        self.assertTrue(result)
#

    def test_get_packages_from_bundle_false(self):
        bundle_yaml = ""
        packages, name, result = curator.get_packages_from_bundle(bundle_yaml)

        self.assertIsNone(packages)
        self.assertEqual(name, 'bundle must have a package object')
        self.assertFalse(result)


class TestPrintingSummary(unittest.TestCase):
    def test_summary_no_results(self):
        summary = []
        with self.assertRaises(IndexError):
            curator.summarize(summary)


    def test_summary_is_list(self):
        summary = {}
        with self.assertRaises(TypeError):
            curator.summarize(summary)


    def test_summary_single_element(self):
        summary = [
            {"testOperator0":
                {"version": "1.0.0",
                 "pass": False,
                 "tests":
                     {"is in allowed list": False}
                }
            }
        ]

        expected_output = (
            "Validation Summary\n" +
            "------------------\n" +
            "\n" +
            "[FAIL] testOperator0 version 1.0.0\n" +
            "    [FAIL] is in allowed list\n" +
            "\n" +
            "Passed: 0\n" +
            "Failed: 1"
        )

        out=StringIO()
        curator.summarize(summary, out=out)
        output = out.getvalue().strip()
        self.assertEqual(output, expected_output)


    def test_summary_no_passes(self):
        summary = [
            {"testOperator0":
                {"version": "1.0.0",
                 "pass": False,
                 "tests":
                     {"is in allowed list": False}
                }
            },
            {"testOperator1":
                {"version": "2.2.40",
                 "pass": False,
                 "tests":
                     {"is in allowed list": False}
                }
            }
        ]

        expected_output = (
            "Validation Summary\n" +
            "------------------\n" +
            "\n" +
            "[FAIL] testOperator0 version 1.0.0\n" +
            "    [FAIL] is in allowed list\n" +
            "\n" +
            "[FAIL] testOperator1 version 2.2.40\n" +
            "    [FAIL] is in allowed list\n" +
            "\n" +
            "Passed: 0\n" +
            "Failed: 2"
        )

        out=StringIO()
        curator.summarize(summary, out=out)
        output = out.getvalue().strip()
        self.assertEqual(output, expected_output)


    def test_summary_output(self):
        summary = [
            {"testOperator0":
                {"version": "1.0.0",
                 "pass": True,
                 "tests":
                     {"is in allowed list": True}
                }
            },
            {"testOperator1":
                {"version": "2.2.40",
                 "pass": True,
                 "tests":
                     {"is in allowed list": True}
                }
            }
        ]

        expected_output = (
            "Validation Summary\n" +
            "------------------\n" +
            "\n" +
            "[PASS] testOperator0 version 1.0.0\n" +
            "    [PASS] is in allowed list\n" +
            "\n" +
            "[PASS] testOperator1 version 2.2.40\n" +
            "    [PASS] is in allowed list\n" +
            "\n" +
            "Passed: 2\n" +
            "Failed: 0"
        )

        out=StringIO()
        curator.summarize(summary, out=out)
        output = out.getvalue().strip()
        self.assertEqual(output, expected_output)

if __name__ == '__main__':
    unittest.main()
