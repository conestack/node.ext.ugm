from setuptools import find_packages
from setuptools import setup
import os


version = '0.9.9.dev0'
shortdesc = "Node-based user and group management"
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'LICENSE.rst')).read()


setup(
    name='node.ext.ugm',
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        'Environment :: Web Environment',
        'Programming Language :: Python',
    ],
    keywords='node user group role',
    author='BlueDynamics Alliance',
    author_email='dev@bluedynamics.com',
    url='https://github.com/bluedynamics/node.ext.ugm',
    license='Simplified BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['node', 'node.ext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'node',
        'plumber'
    ],
    extras_require={
        'test': [
            'zope.testing'
        ]
    },
    test_suite='node.ext.ugm.tests.test_suite',
    entry_points="""
    """
)
