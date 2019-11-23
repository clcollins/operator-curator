"""
This module summarizes test results and returns a report to stdout.
"""

import sys


class Summary:
    """
    This class represents a summary object that can be
    used to generate a report.
    """

    def __init__(self):
        self.report = []

    def summarize(self, out=sys.stdout):
        """
        Summarize prints a summary of results for human readability.
        """

        if not isinstance(self.report, list):
            raise TypeError()
        if not self.report:
            raise IndexError()

        report = []

        passing_count = len(
            [
                i for i in self.report if {
                    key: value for (key, value) in i.items() if (
                        value["pass"]
                    )
                }
            ]
        )
        skipped_count = len(
            [
                i for i in self.report if {
                    key: value for (key, value) in i.items() if (
                        value["skipped"]
                    )
                }
            ]
        )

        # TODO: This should be replaced with a template of some kind
        for i in self.report:
            for operator, info in i.items():
                operator_result = "[PASS]" if info["pass"] else "[FAIL]"
                report.append(
                    f"\n{operator_result} {operator} "
                    f"version {info['version']}"
                )
                for name, result in info["tests"].items():
                    test_result = (
                        "[SKIP]" if info["skipped"] else (
                            "[PASS]" if result else "[FAIL]"))
                    report.append(f"    {test_result} {name}")

        report_str = "\n".join(report)

        # Not as readable as printing, but prepping for unittesting
        out.write(
            f"\nValidation Summary\n"
            f"------------------\n"
            f"{report_str}\n"
            f"\n"
            f"Passed Curation: {passing_count - skipped_count}\n"
            f"Already Curated: {skipped_count}\n"
            f"Failed Curation: {len(self.report) - passing_count}\n"
        )
