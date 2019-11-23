def validate_csv(csv):
    """
    Validates a specific clusterServiceVersion object against curation
    rules.
    """

    tests = {}

    tests['requires clusterPermissions'] = (
        True if csv.requires_cluster_permissions else False)

    tests['requires securityContextConstraints'] = (
        True if csv.requires_security_context_constraints else False)

    tests['allows_multinamespace_install_mode'] = (
        True if csv.allows_multinamespace_install_mode else False)

    if True in tests.values():
        return True, tests

    return False, tests


def validate_pacakge_release(release):
    """
    Validates a specific package release object against curation rules.
    """

    tests = {}
    tests['release has already been curated'] = (
        True if release.already_curated else False
    )

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

    tests['package is in denied list'] = (
        True if pkg.is_in_denied_list else False)

    tests['package is in allowed list'] = (
        True if pkg.is_in_allowed_list else False)

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
