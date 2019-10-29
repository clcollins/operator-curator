#!/usr/bin/env python3
"""
The app registry curator is a tool that scans Quay.io app registries in order to vet operators for use with OSD v4.
"""

import argparse
import base64
import json
import logging
from pathlib import Path
import tarfile
import shutil
import sys
import requests
import yaml


SOURCE_NAMESPACES = [
    "redhat-operators",
    "certified-operators",
    "community-operators"
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
    return "https://quay.io/cnr/api/v1/" + path


def _repo_url(path):
    return "https://quay.io/api/v1/" + path


def _quay_headers(authtoken):
    return {
        "Authorization" : authtoken,
        "Content-Type": "application/json"
    }


def _pkg_shortname(package):
    ''' Strips out the package's namespace and returns its shortname '''
    return package.split('/')[1]


def list_operators(namespace):
    '''List the operators in the provided quay app registry namespace'''
    r = requests.get(_url(f"packages?namespace={namespace}"))
    if r.ok:
        l = [str(e['name']) for e in r.json()]
        return l

    return None


def get_release_data(operator):
    """
    Gets all the release versions for an operator package,
    eg: redhat-operators/codeready-workspaces, and returns a dictionary
    of release version, package name, and its digests.
    """
    releases = {}
    r = requests.get(_url(f"packages/{operator}"))
    if r.ok:
        for release in r.json():
            releases[str(release['release'])] = {
                "digest": str(release['content']['digest']),
                "package": release['package']
            }
    return releases


def set_repo_visibility(namespace, package_shortname, oauth_token, public=True,):
    '''Set the visibility of the specified app registry in Quay.'''
    s = requests.sessions.Session()

    visibility = "public" if public else "private"

    logging.info(f"Setting visibility of {namespace}/{package_shortname} to {'public' if public else 'private'}")

    try:
        r = s.post(
            _repo_url(f"repository/{namespace}/{package_shortname}/changevisibility"),
            json={"visibility": visibility},
            headers=_quay_headers(f"Bearer {oauth_token}")
        )
        r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        logging.error(f"Failed to set visibility of {namespace}/{package_shortname}. HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        logging.error(f"Failed to set visibility of {namespace}/{package_shortname}. Connection Error: {errc}")
    except requests.exceptions.Timeout as errt:
        logging.error(f"Failed to set visibility of {namespace}/{package_shortname}. Timeout Error: {errt}")


def get_package_release(release, use_cache):
    """
    Downloads the tarball package for the release.
    """
    if use_cache:
        return

    r = requests.get(_url(f"packages/{release['package']}/blobs/sha256/{digest}"))
    outfile = Path(f"{release['package']}/{release['version']}/{_pkg_shortname(release['package'])}.tar.gz")

    try:
        with open(outfile, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    finally:
        del r


def check_package_in_allow_list(package):
    """
    Returns true if the packaged has been listed in the allow list,
    regardless of other heuristics.  Also returns the test name.
    """
    test_name = 'is in allowed list'
    if package in ALLOWED_PACKAGES:
        return test_name, True

    return test_name, False


def check_package_in_deny_list(package):
    """
    Returns true if the packaged has been listed in the denly list,
    regardless of other heuristics.  Also returns the test name.
    """
    test_name = 'is in denied list'
    if package in DENIED_PACKAGES:
        return test_name, True

    return test_name, False


def extract_bundle_from_tar_file(tarfile):
    """
    Extracts the bundle.yaml file from the tar object provides.
    Returns the bundle.yaml object, test name, and result.
    """

    test_name = 'bundle.yaml must be present'
    with tarfile.open(tarfile) as t:
        try:
            bundle_file = t.extractfile([i for i in t if Path(i.name).name == "bundle.yaml"][0])
        except:
            bundle_file = None
            result = False
        else:
            result = True
        finally:
            return bundle_file, test_name, result


def load_yaml_from_bundle_object(bundle_yaml_obj):
    """
    Loads the yaml from the bundle object and returns a failure if
    it is unable to.  Also returns the test name and result.
    """

    test_name = 'bundle.yaml must be parsable'
    try:
        bundle_yaml = yaml.safe_load(bundle_yaml_obj.read())
    except yaml.YAMLError:
        bundle_yaml = None
        result = False
    else:
        result = True
    finally:
        return bundle_yaml, test_name, result


def get_packages_from_bundle(bundle_yaml):
    """
    Tests whether or not packages are contained in the bundle.yaml,
    and returns them if so, and returns the test name and result.
    """

    test_name = "bundle must have a package object"
    try:
        packages = bundle_yaml['data']['packages']
    except:
        packages = None
        result = False
    else:
        result = True
    finally:
        return packages, test_name, result


def check_clusterserviceversion(package, version, csv):
    """
    Checks csv to make sure there are no clusterPermissions,
    it does not support multi-namespace install mode,
    and it does not require security context constraints
    """

    # Aggregates CSV sub-tests, returns dict of results
    # test_name =
    # return [X], test_name, result

    check_csv_for_clusterpermissions()
    check_csv_for_securitycontextconstraints()
    check_csv_for_multinamespace_installmode()

    tests = {}
    # Cluster Permissions aren't allowed
    cpKey = "CSV must not include clusterPermissions"
    tests[cpKey] = True
    if 'clusterPermissions' in csv['spec']['install']['spec']:
        logging.info(f"[FAIL] {package} version {version} requires clusterPermissions")
        tests[cpKey] = False
    # Using SCCs isn't allowed
    sccKey = "CSV must not grant SecurityContextConstraints permissions"
    tests[sccKey] = True
    if 'permissions' in csv['spec']['install']['spec']:
        for rules in csv['spec']['install']['spec']['permissions']:
            for i in rules['rules']:
                if ("security.openshift.io" in i['apiGroups'] and
                        "use" in i['verbs'] and
                        "securitycontextconstraints" in i['resources']):
                    logging.info(f"[FAIL] {package} version {version} requires security context constraints")
                    tests[sccKey] = False
    # installMode == MultiNamespace is not allowed
    multiNsKey = "CSV must not require MultiNamespace installMode"
    tests[multiNsKey] = True
    for im in csv['spec']['installModes']:
        if im['type'] == "MultiNamespace" and im['supported'] is True:
            logging.info(f"[FAIL] {package} version {version} supports multi-namespace install mode")
            tests[multiNsKey] = False

    result = bool(all(tests.values()))
    return result, tests


def validate_bundle(release):
    """
    Review the bundle.yaml for a package to check that it is
    appropriate for use with OSD.
    """
    package = release['package']
    version = release['version']

    tests = {}
    csvsByChannel = {}
    truncatedBundle = False
    bundle_filename = "bundle.yaml"
    bundle_file = Path(f"./{package}/{version}/{bundle_filename}")

    logging.info(f"Validating bundle for {package} version {version}")

    shortname = _pkg_shortname(package)

    # Any package in our allow list is valid, regardless of other heuristics
    name, result = check_package_in_allow_list(package)
    tests[name] = result
    logging.info(f"{'[PASS] if result else [FAIL]'} {package} (all versions) {name}")

    if result:
        return True, tests


    # Any package in our deny is invalid; skip further processing
    name, result = check_package_in_deny_list(package)
    tests[name] = result
    logging.info(f"{'[FAIL] if result else [PASS]'} {package} (all versions) {name}")

    if result:
        return False, tests


    # Extract the bundle.yaml file
    bundle_yaml_object, name, result = extract_bundle_from_tar_file(
        f"{package}/{version}/{shortname}.tar.gz")

    tests[name] = result
    logging.info(f"{'[PASS] if result else [FAIL]'} {package} (all versions) {name}")

    # If extracting the bundle fails, no further processing is possible
    if not result:
        return False, tests


    # Load the yaml from the bundle object to a variable
    bundle_yaml, name, result = load_yaml_from_bundle_object(bundle_yaml_object)
    tests[name] = result
    logging.info(f"{'[PASS] if result else [FAIL]'} {package} (all versions) {name}")

    # If reading the yaml file fails, no further processing is possible
    if not result:
        return False, tests

    # Retrieve the package list from the bundle
    packages, name, result = get_packages_from_bundle(bundle_yaml)
    tests[name] = result
    logging.info(f"{'[PASS] if result else [FAIL]'} {package} (all versions) {name}")


    # TODO: create function for testing custom resource definitions
    # name, result = test_custom_resource_definitions(bundle_yaml['data']['customResourceDefinitions'])

    # The package might have multiple channels, loop thru them
    for channel in packages[0]['channels']:
        good_csvs = [] # What is this used for?

        # Test the most recent CSV in the channel
        latest_channel_csv = get_csv_from_name(csvs, channel['currentCSV'])
        name, csv_test_results = check_clusterserviceversion(latest_channel_csv)

        # META_CODE
        # if any of the tests in the test result failed, reject the whole thing
        # if any False in test_results:
        name, result = check_test_results_for_failures(csv_test_results)
        tests[name] = result
        logging.info(f"{'[PASS] if result else [FAIL]'} {package} (all versions) {name}")

        # Add CSV test results to overall test results
        tests.update(csv_test_results)


        # TODO: REPLICATE THIS
        # there are channels in each package "package[0]['channels']"
        # for each channel:
        # get the latestCSVname: channel['currentCSV']
        # use the name to get the csv (get_csv_from_name(csvs, latestCSVname))
        # test the clusterserviceversion of the latet csv
        # if the latest csv doesnt pass
        # reject entire thing (return false, tests)
        # else "latestBundleKey" test is a pass - add to test lists
        #    good_csvs.append(latestCSV)
        #latestBundleKey = f"CSV {latestCSV['metadata']['name']} curated"
        #
        # Next, tests "latestCSV['spec'].get('replaces)"
        # (if not 'None')
        # if not passes, truncate bundle using list of good csvs
        # and break
        # else:
        #        good_csvs.append(nextCSV)
        #        nextCSVPassKey = f"CSV {replacesCSVName} curated"
        #        get next csv from 'replaces'
        #        nextCSV = get_csv_from_name(csvs, replacesCSVName)
        #        replacesCSVName = nextCSV.get('replaces')
        # Last:  add good_csvs list to
        #        csvsByChannel[channel['name']] = good_csvs

        # If the bundle was truncated we need to regen the bundle file and links
        if truncatedBundle:
            logging.warning(f"{package} version {version} - writing truncated bundle to tarfile")
            by = regenerate_bundle_yaml(
                by,
                packages,
                customResourceDefinitions,
                csvsByChannel)

            with open(bundle_file, 'w') as outfile:
                yaml.dump(by, outfile, default_style='|')

            # Create tar.gz file, forcing the bundle file to sit in the root of the tar vol
            with tarfile.open(f"{package}/{version}/{shortname}.tar.gz", "w:gz") as tar_handle:
                tar_handle.add(bundle_file, arcname=bundle_filename)

    # If all of the values for dict "tests" are True, return True
    # otherwise return False (operator validation has failed!)
    result = bool(all(tests.values()))
    return result, tests


def regenerate_bundle_yaml(bundle_yaml, packages,
                           customResourceDefinitions, csvsByChannel):
    """
    Regenerates the bundle yaml with curated CSV data
    """
    csvs = []
    # For every channel, carry over the curated CSVs, and reset the 'replaces' field for the last one
    for channel in csvsByChannel:
        channelCSVs = csvsByChannel[channel]

        channelCSVs[-1]['spec'].pop('replaces', None)
        csvs += channelCSVs

    # Override CSVs in the original bundle, default to pipe delimited valus to support longer fields
    bundle_yaml['data']['clusterServiceVersions'] = yaml.dump(csvs, default_style='|')
    bundle_yaml['data']['customResourceDefinitions'] = yaml.dump(customResourceDefinitions, default_style='|')
    bundle_yaml['data']['packages'] = yaml.dump(packages, default_style='|')

    return bundle_yaml


def get_csv_from_name(csvs, csvName):
    """
    Returns a cluster service version from the csv name
    """
    for csv in csvs:
        if csv['metadata']['name'] == csvName:
            return csv

    return None


def push_package(package, version, target_namespace, oauth_token, basic_token, skip_push):
    '''
    Push package on disk into a target quay namespace.
    '''
    shortname = _pkg_shortname(package)

    if skip_push:
        logging.debug(f"Not pushing package {shortname} to namespace {target_namespace}")
        return

    # Don't try to push if the specific package version is already present in our target namespace
    target_releases = get_package_releases(f"{target_namespace}/{shortname}")
    if version in target_releases.keys():
        logging.info(f"Version {version} of {shortname} is already present in {target_namespace} namespace. Skipping...")
        return

    with open(f"{package}/{version}/{shortname}.tar.gz") as f:
        encoded_bundle = base64.b64encode(f.read())

    payload = {
        "blob": encoded_bundle,
        "release": version,
        "media_type": "helm"
    }

    try:
        logging.info(f"Pushing {shortname} to the {target_namespace} namespace")
        r = requests.post(_url(f"packages/{target_namespace}/{shortname}"), data=json.dumps(payload), headers=_quay_headers(basic_token))
        r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        if r.status_code == 409:
            logging.info(f"Version {version} of {shortname} is already present in {target_namespace} namespace. Skipping...")
        else:
            logging.error(f"Failed to upload {shortname} to {target_namespace} namespace. HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        logging.error(f"Failed to upload {shortname} to {target_namespace} namespace. Connection Error: {errc}")
    except requests.exceptions.Timeout as errt:
        logging.error(f"Failed to upload {shortname} to {target_namespace} namespace. Timeout Error: {errt}")

    # If this is a new package namespace, make it publicly visible
    if target_releases.keys():
        set_repo_visibility(target_namespace, shortname, oauth_token)


def summarize(summary, out=sys.stdout):
    """Summarize prints a summary of results for human readability."""

    if not type(summary) == list:
        raise TypeError()
    if not summary:
        raise IndexError()


    report = []

    passing_count = len([i for i in summary if {key:value for (key, value) in i.items() if value["pass"]}])
    for i in summary:
        for operator, info in i.items():
            operator_result = "[PASS]" if info["pass"] else "[FAIL]"
            report.append(f"\n{operator_result} {operator} version {info['version']}")
            for name, result in info["tests"].items():
                test_result = "[PASS]" if result else "[FAIL]"
                report.append(f"    {test_result} {name}")

    report_str = "\n".join(report)

    # Not as readable as printing, but prepping for unittesting
    out.write(
        "\nValidation Summary\n" +
        "------------------\n" +
        f"{report_str}\n"
        "\n" +
        f"Passed: {passing_count}\n" +
        f"Failed: {len(summary) - passing_count}\n"
    )


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser(description="A tool for curating application registry for use with OSDv4")
    PARSER.add_argument('--app-token', action="store", dest="basic_token",
                        type=str, help="Basic auth token for use with Quay's CNR API")
    PARSER.add_argument('--oauth-token', action="store", dest="oauth_token",
                        type=str, help="Oauth token for use with Quay's repository API")
    PARSER.add_argument('--cache', action="store_true", default=False, dest="use_cache",
                        help="Use local cache of operator packages")
    PARSER.add_argument('--skip-push', action="store_true", default=False, dest="skip_push",
                        help="Skip pushing validated packages to Quay.io")

    ARGS = PARSER.parse_args()

    logging.basicConfig(level=logging.INFO)

    SUMMARY = []

    for ns in SOURCE_NAMESPACES:
        for operator in list_operators(ns):
            release_data = get_release_data(operator)
            for release in release_data:
                get_package_release(release, ARGS.use_cache)
                passed, info = validate_bundle(release)
                SUMMARY.append({operator: {"version": release_version, "pass": passed, "tests": info}})
                if passed:
                    logging.info(f"{operator} version {release_version} is a valid operator for use with OSD")
                    push_package(operator, release_version, f"curated-{ns}", ARGS.oauth_token, ARGS.basic_token, ARGS.skip_push)
                else:
                    logging.info(f"{operator} version {release_version} FAILED VALIDATION for use with OSD")

    summarize(SUMMARY)
