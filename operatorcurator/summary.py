"""
This module summarizes test results and returns a report to stdout.
"""

import sys


def count_versions_by_key(key, report):
    """
    Return the count of release versions in a report that contain
    a specified key.
    """
    count = 0
    for pkg in report:
        count += len(
            [
                [
                    version for version in value if (
                        version[key]
                    )
                ] for (_, value) in pkg.items()
            ][0]
        )

    return count


class Summary:
    """
    This class represents a summary object that can be
    used to generate a report.
    """

    def __init__(self, report):
        self.summary = []
        self.report = report

    def summarize(self, out=sys.stdout):
        """
        Summarize prints a summary of results for human readability.
        """

        if not isinstance(self.report, list):
            raise TypeError()
        if not self.report:
            raise IndexError()

        passing_count = count_versions_by_key('pass', self.report)
        skipped_count = count_versions_by_key('skipped', self.report)
        total_count = count_versions_by_key('version', self.report)

        self.summary = []

        # TODO: This should be replaced with a template of some kind
        for i in self.report:
            for operator, info in i.items():
                for version in info:
                    version_result = "[PASS]" if version["pass"] else "[FAIL]"
                    self.summary.append(
                        f"\n{version_result} {operator} "
                        f"version {version['version']}"
                    )
                    for name, result in version["tests"].items():
                        test_result = (
                            "[SKIP]" if version["skipped"] else (
                                "[PASS]" if result else "[FAIL]"))
                        self.summary.append(f"    {test_result} {name}")

        summary_output = "\n".join(self.summary)

        # Not as readable as printing, but prepping for unittesting
        out.write(
            f"\nValidation Summary\n"
            f"------------------\n"
            f"{summary_output}\n"
            f"\n"
            f"Passed Curation: {passing_count - skipped_count}\n"
            f"Already Curated: {skipped_count}\n"
            f"Failed Curation: {total_count - passing_count}\n"
        )
