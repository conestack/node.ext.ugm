import unittest
import sys


def test_suite():
    from node.ext.ugm.tests import test_api
    from node.ext.ugm.tests import test_file

    suite = unittest.TestSuite()

    suite.addTest(unittest.findTestCases(test_api))
    suite.addTest(unittest.findTestCases(test_file))

    return suite


def run_tests():
    from zope.testrunner.runner import Runner

    runner = Runner(found_suites=[test_suite()])
    runner.run()
    sys.exit(int(runner.failed))


if __name__ == '__main__':
    run_tests()
