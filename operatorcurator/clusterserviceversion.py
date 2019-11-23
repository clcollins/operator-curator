import yaml
import logging
from .validate import validate_csv

logger = logging.getLogger(__name__)

def _parse_scc_from_rules(rule):
    """
    Checks if securitycontextconstraints exist with use or '*'
    verbs in a clusterServiceVersion permission rule.
    """

    is_scc_related = (
        'security.openshift.io' in rule['apiGroups'] and
        'securitycontextconstraints' in rule['resources']
    )

    logger.debug(f"rule is_scc_related: {is_scc_related}")

    has_disallowed_verbs = (
        'use' in rule['verbs'] or
        '*' in rule['verbs']
    )

    logger.debug(f"rule has_disallowed_verbs: {has_disallowed_verbs}")

    # Only returns True if both are True
    return is_scc_related and has_disallowed_verbs


class ClusterServiceVersion:
    """
    Represents a ClusterServiceVersion object.
    """

    def __init__(self, csv_yaml):
        self.yaml = csv_yaml

        self.name = self.yaml['metadata']['name']
        self.version = self.yaml['spec']['version']
        logging.debug(f"CSV: {self.name}")


        # TODO: Need to figure this out
        self.is_latest = False
        logger.debug(f"CSV is_latest: {self.is_latest}")

        # Check if this CSV requires clusterPermissions
        self.requires_cluster_permissions = (
            self.check_cluster_permissions(self.yaml)
        )
        logger.debug(
            f"CSV requires_cluster_permissions: "
            f"{self.requires_cluster_permissions}"
        )

        # Check if this CSV requires securityContextConstraints
        self.requires_security_context_constraints = (
            self.check_security_context_constraints(self.yaml)
        )
        logger.debug(
            f"CSV requires_security_context_constraints: "
            f"{self.requires_security_context_constraints}"
        )

        # Check if this CSV allows multiNamespace installMode
        self.allows_multinamespace_install_mode = (
            self.check_multinamespace_install_mode(self.yaml)
        )
        logger.debug(
            f"CSV allows_multinamespace_install_mode: "
            f"{self.allows_multinamespace_install_mode}"
        )

        self.valid, self.tests = validate_csv(self)
        logger.debug(f"CSV is_valid: {self.valid}")


    def check_cluster_permissions(self, csv_yaml):
        """
        Checks whether or not the CSV requires cluster permissions.
        """

        spec = csv_yaml['spec']['install']['spec']

        return True if 'clusterPermissions' in spec else False


    def check_security_context_constraints(self, csv_yaml):
        """
        Checks whether or not the CSV requires cluster permissions.
        """

        spec = csv_yaml['spec']['install']['spec']
        permissions = (
            spec['permissions'] if 'permissions' in spec.keys() else None
        )

        if permissions:
            for permission in permissions:
                rule = permission['rules'][0]

                if _parse_scc_from_rules(rule):
                    return True

        return False


    def check_multinamespace_install_mode(self, csv_yaml):
        """
        Checked whether or not the CSV allows multiNamespace installMode.
        """

        install_modes = csv_yaml['spec']['installModes']

        for mode in install_modes:
            if mode['type'] == 'MultiNamespace' and mode['supported']:
                return True

        return False
