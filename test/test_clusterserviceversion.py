"""
Tests the clusterServiceVersion module.
"""

import unittest
import yaml
from operatorcurator import clusterserviceversion as CSV


class TestClusterServiceVersion(unittest.TestCase):
    """
    Tests for the clusterServiceVersion object.
    """

    def get_test_yaml(self, yaml_file):
        """
        Tests loading and returning yaml correctly.
        """
        with open(yaml_file, 'r') as yaml_file:
            test_yaml = yaml.safe_load(yaml_file)

        return test_yaml

    def test_init(self):
        """
        Tests initialization of the object from yaml.
        """
        test_yaml = self.get_test_yaml(
            "test/data/example_clusterserviceversion.yaml"
        )

        test_csv = CSV.ClusterServiceVersion(test_yaml)

        self.assertEqual(test_csv.yaml, test_yaml)

    def test_check_for_cluster_permissions_pass(self):
        """
        Tests passing results for clusterPermissions checking.
        """
        test_yaml = self.get_test_yaml(
            "test/data/example_clusterserviceversion.yaml"
        )

        test_csv = CSV.ClusterServiceVersion(test_yaml)

        self.assertFalse(test_csv.requires_cluster_permissions)

    def test_check_for_cluster_permissions_fail(self):
        """
        Tests failing results for clusterPermissions checking.
        """
        test_yaml = self.get_test_yaml(
            "test/data/example_clusterserviceversion.yaml"
        )

        # Patch the csv yaml to add clusterPermissions
        install_spec = test_yaml['spec']['install']['spec']
        install_spec['clusterPermissions'] = True
        test_csv = CSV.ClusterServiceVersion(test_yaml)

        self.assertTrue(test_csv.requires_cluster_permissions)

    def test_parse_scc_from_rules_fail(self):
        """
        Tests failing checks for existence of scc item in a rule.
        """
        rule = {
            'apiGroups': ['security.openshift.io'],
            'resources': ['securitycontextconstraints'],
            'verbs': ['use']
        }

        self.assertTrue(CSV.parse_scc_from_rules(rule))

        rule = {
            'apiGroups': ['security.openshift.io'],
            'resources': ['securitycontextconstraints'],
            'verbs': ['*']
        }

        self.assertTrue(CSV.parse_scc_from_rules(rule))

        rule = {
            'apiGroups': ['security.openshift.io'],
            'resources': ['securitycontextconstraints'],
            'verbs': ['use', '*']
        }

        self.assertTrue(CSV.parse_scc_from_rules(rule))

        rule = {
            'apiGroups': ['security.openshift.io'],
            'resources': ['securitycontextconstraints'],
            'verbs': ['use', 'get']
        }

        self.assertTrue(CSV.parse_scc_from_rules(rule))

        rule = {
            'apiGroups': ['security.openshift.io'],
            'resources': ['securitycontextconstraints'],
            'verbs': ['get', '*']
        }

        self.assertTrue(CSV.parse_scc_from_rules(rule))

        rule = {
            'apiGroups': ['security.openshift.io'],
            'resources': ['securitycontextconstraints'],
            'verbs': ['use', 'get', '*']
        }

        self.assertTrue(CSV.parse_scc_from_rules(rule))

    def test_parse_scc_from_rules_pass(self):
        """
        Tests passing checks for existence of scc item in a rule.
        """
        rule = {
            'apiGroups': ['security.openshift.io'],
            'resources': ['securitycontextconstraints'],
            'verbs': ['list']
        }

        self.assertFalse(CSV.parse_scc_from_rules(rule))

        rule = {
            'apiGroups': ['security.openshift.io'],
            'resources': ['roles'],
            'verbs': ['use']
        }

        self.assertFalse(CSV.parse_scc_from_rules(rule))

        rule = {
            'apiGroups': ['rbac.authorization.k8s.io'],
            'resources': ['securitycontextconstraints'],
            'verbs': ['use']
        }

        self.assertFalse(CSV.parse_scc_from_rules(rule))

    def test_check_for_security_context_constraints_pass(self):
        """
        Tests passing results for securityContextConstraints checking.
        """
        test_yaml = self.get_test_yaml(
            "test/data/example_clusterserviceversion.yaml"
        )

        test_csv = CSV.ClusterServiceVersion(test_yaml)

        self.assertFalse(test_csv.requires_security_context_constraints)

    def test_check_for_security_context_constraints_fail(self):
        """
        Tests failing results for securityContextConstraints checking.
        """
        test_yaml = self.get_test_yaml(
            "test/data/example_clusterserviceversion.yaml"
        )

        # Patch the csv yaml to add sccs
        install_spec = test_yaml['spec']['install']['spec']
        install_spec['permissions'] = [
            {
                'serviceAccountName': 'robot',
                'rules':
                    [
                        {
                            'apiGroups': ['security.openshift.io'],
                            'resources': ['securitycontextconstraints'],
                            'verbs': ['use']
                        }
                    ]
            }
        ]

        install_spec['securityContextConstraints'] = True
        test_csv = CSV.ClusterServiceVersion(test_yaml)

        self.assertTrue(test_csv.requires_security_context_constraints)

    def test_check_for_multinamepsace_install_mode_pass(self):
        """
        Tests passing results for multiNamespace installMode lookup checking.
        """
        test_yaml = self.get_test_yaml(
            "test/data/example_clusterserviceversion.yaml"
        )

        test_csv = CSV.ClusterServiceVersion(test_yaml)

        self.assertFalse(test_csv.allows_multinamespace_install_mode)

    def test_check_for_multinamepsace_install_mode_fail(self):
        """
        Tests failing results for multiNamespace installMode lookup checking.
        """
        test_yaml = self.get_test_yaml(
            "test/data/example_clusterserviceversion.yaml"
        )

        # Patch the csv yaml to enable MultiNamespace
        test_yaml['spec']['installModes'] = [
            {
                'type': 'OwnNamespace',
                'supported': True
            },
            {
                'type': 'SingleNamespace',
                'supported': True
            },
            {
                'type': 'MultiNamespace',
                'supported': True
            },
            {
                'type': 'AllNamespaces',
                'supported': False
            },
        ]

        test_csv = CSV.ClusterServiceVersion(test_yaml)

        self.assertTrue(test_csv.allows_multinamespace_install_mode)

        # Patch the csv yaml to enable AllNamespaces
        test_yaml['spec']['installModes'] = [
            {
                'type': 'OwnNamespace',
                'supported': True
            },
            {
                'type': 'SingleNamespace',
                'supported': True
            },
            {
                'type': 'MultiNamespace',
                'supported': False
            },
            {
                'type': 'AllNamespaces',
                'supported': True
            },
        ]

        test_csv = CSV.ClusterServiceVersion(test_yaml)

        self.assertFalse(test_csv.allows_multinamespace_install_mode)
