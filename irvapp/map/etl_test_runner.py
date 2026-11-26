"""Make the dedicated ETL CI invocation fail if tests are absent or skipped."""
import logging

from django.test.runner import DiscoverRunner


class ETLTestRunner(DiscoverRunner):
    def suite_result(self, suite, result, **kwargs):
        failures = super().suite_result(suite, result, **kwargs)
        if result.testsRun == 0 or result.skipped:
            self.log("ETL tests must run without skips.", level=logging.ERROR)
            return failures + 1
        return failures
