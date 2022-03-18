from setuptools import find_packages
from setuptools import setup
from setuptools.command.test import test
import os


def read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return f.read()


version = '1.0'
shortdesc = "Node-based user and group management"
longdesc = '\n\n'.join([read_file(name) for name in [
    'README.rst',
    'CHANGES.rst',
    'LICENSE.rst'
]])


class Test(test):

    def run_tests(self):
        from node.ext.ugm import tests
        tests.run_tests()


setup(
    name='node.ext.ugm',
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
    keywords='node user group role',
    author='Node Contributors',
    author_email='dev@conestack.org',
    url='https://github.com/conestack/node.ext.ugm',
    license='Simplified BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['node', 'node.ext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'node>=1.0',
        'setuptools'
    ],
    extras_require=dict(
        test=[
            'zope.testrunner'
        ]
    ),
    tests_require=[
        'zope.testrunner'
    ],
    cmdclass=dict(test=Test)
)
