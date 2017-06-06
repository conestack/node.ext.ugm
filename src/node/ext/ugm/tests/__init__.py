from node.tests import NodeTestCase
import unittest


def test_suite():
    from node.ext.ugm.tests import test_api
    from node.ext.ugm.tests import test_file

    suite = unittest.TestSuite()

    suite.addTest(unittest.findTestCases(test_api))
    suite.addTest(unittest.findTestCases(test_file))

    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True)
    runner.run(test_suite())
