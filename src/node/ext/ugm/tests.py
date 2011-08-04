import doctest
import interlude
import pprint
import unittest2 as unittest


DOCFILES = [
    '__init__.rst',
    '_api.rst',
    'file.rst',
]

optionflags = doctest.NORMALIZE_WHITESPACE | \
              doctest.ELLIPSIS | \
              doctest.REPORT_ONLY_FIRST_FAILURE


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        doctest.DocFileSuite(
            docfile,
            globs={'interact': interlude.interact,
                   'pprint': pprint.pprint,
                   'pp': pprint.pprint,
            },
            optionflags=optionflags,
            )
        for docfile in DOCFILES
        ])
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')                 #pragma NO COVERAGE