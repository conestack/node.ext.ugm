from setuptools import setup, find_packages
import sys, os

version = '0.9pre2'
shortdesc = "Node-based user and group management"
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'LICENSE.rst')).read()

setup(name='node.ext.ugm',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
            'Environment :: Web Environment',
            'Framework :: Zope2',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',            
      ], # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='BlueDynamics Alliance',
      author_email='dev@bluedynamics.com',
      url='https://github.com/bluedynamics/node.ext.ugm',
      license='General Public Licence',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['node', 'node.ext'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'node',
          'plumber',
          'setuptools',
      ],
      extras_require={
          'test': [
              'interlude',
              'unittest2',
              'zope.testing',        
          ]
      },
      entry_points="""
      """,
      )
