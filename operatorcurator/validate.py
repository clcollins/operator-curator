"""
Contains all the validation tests for specific object types, to aggregate
them into one place.
"""


def validate_csv(csv):
    """
    Validates a specific clusterServiceVersion object against curation
    rules.
    """

    tests = {}

    tests['requires clusterPermissions'] = bool(
        csv.requires_cluster_permissions
    )

    tests['requires securityContextConstraints'] = bool(
        csv.requires_security_context_constraints
    )

    tests['allows multiNamespace installMode'] = bool(
        csv.allows_multinamespace_install_mode
    )

    # If any of the above are True, csv is INVALID
    if True in tests.values():
        return False, tests

    # Otherwise, csv is OK
    return True, tests


def validate_pacakge_release(release):
    """
    Validates a specific package release object against curation rules.
    """

    tests = {}
    tests['release has already been curated'] = bool(release.already_curated)

    if tests['release has already been curated']:
        return True, tests

    # Extract bundle from yaml, or csv from  yaml
    # Yaml must be parsable
    # Get packages from bundle.yaml ?!  <-- what are these
    # Get csvs from bundledd
    # Latest CSV doesn't pass curation, Fail

    return True, tests


def validate_package(pkg):
    """
    Validates a specific package object against curation
    rules.
    """

    tests = {}

    tests['package is in denied list'] = bool(pkg.is_in_denied_list)

    tests['package is in allowed list'] = bool(pkg.is_in_allowed_list)

    # If not in either list, it's valid
    if not tests[
            'package is in allowed list'
    ] and not tests[
        'package is in denied list'
    ]:
        return True, tests

    # If only in allowed list, it's valid
    if tests[
            'package is in allowed list'
    ] and not tests[
        'package is in denied list'
    ]:
        return True, tests

    # Both other cases: allowed and denied, and just denied, are invalid
    return False, tests
