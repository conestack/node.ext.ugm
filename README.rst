User and group management
=========================

``node.ext.ugm`` provides an API for node based managing of users and groups.

See ``node.ext.ugm.interfaces`` for a description of the API.

A file based default implementation can be found at ``node.ext.ugm.file``.

Base objects for writing UGM implementations can be found at
``node.ext.ugm._api``.

For more information on nodes see `node <http://pypi.python.org/pypi/node>`_
package.

For more information on plumbing see
`plumber <http://pypi.python.org/pypi/plumber>`_ package.


TestCoverage
============

.. image:: https://travis-ci.org/bluedynamics/node.ext.ugm.svg?branch=master
    :target: https://travis-ci.org/bluedynamics/node.ext.ugm

Summary of the test coverage report::

    Name                                                    Stmts   Miss  Cover
    ---------------------------------------------------------------------------
    src/node/ext/ugm/__init__.py                               18      0   100%
    src/node/ext/ugm/_api.py                                   98      0   100%
    src/node/ext/ugm/file.py                                  464      0   100%
    src/node/ext/ugm/interfaces.py                             34      0   100%
    src/node/ext/ugm/tests/__init__.py                         12      0   100%
    src/node/ext/ugm/tests/test_api.py                        197      0   100%
    src/node/ext/ugm/tests/test_file.py                       459      0   100%
    ---------------------------------------------------------------------------
    TOTAL                                                    1282      0   100%


Python Versions
===============

- Python 2.7, 3.3+, pypy

- May work with other versions (untested)


Contributors
============

- Robert Niederreiter

- Florian Friesdorf


Changes
=======

0.9.9
-----

- ``node.ext.ugm.file.FileStorage`` no longer provides ``unicode_keys`` and
  ``unicode_values``, files are always read and written encoded by encoding
  defined at ``node.ext.ugm.file.ENCODING``, keys and values are always decoded
  to unicode on read.
  [rnix, 2017-06-07]

- Python 3 Support.
  [rnix, 2017-06-07]


0.9.8
-----

- Fix bug where non related principal data has been overwritten when adding
  principal on partial loaded ugm tree.
  [rnix, 2015-04-12]

- Also delete user and group corresponding data if user or group is deleted.
  [rnix, 2015-04-11]

- Fix ``node.ext.ugm.file.UsersBehavior.passwd`` behavior.
  [rnix, 2015-04-11]


0.9.7
-----

- Create user and group data directories recursiv if not exists.
  [rnix, 2014-12-02]


0.9.6
-----

- Encode plain passwd for comparing with hash.
  [rnix, 2014-09-10]


0.9.5
-----

- Use ``plumbing`` decorator instead of ``plumber`` metaclass.
  [rnix, 2014-08-01]


0.9.4
-----

- Use better password hashing for file based default UGM implementation.
  **Warning** - all existing passwords in user table do not work any longer
  and must be reset.
  [rnix, 2014-06-13]


0.9.3
-----

- Rename parts to behaviors.
  [rnix, 2012-07-29]

- adopt to ``node`` 0.9.8.
  [rnix, 2012-07-29]

- Adopt to ``plumber`` 1.2.
  [rnix, 2012-07-29]

- Add ``User.group_ids``.
  [rnix, 2012-07-26]


0.9.2
-----

- Remove outdated stuff.
  [rnix, 2012-05-18]

- Use ``zope.interface.implementer`` instead of ``zope.interface.implements``.
  [rnix, 2012-05-18]


0.9.1
-----

- add ``Users.id_for_login``.
  [rnix, 2012-01-18]

- Implement ``search`` function for file based UGM as described in interface.
  [rnix, 2011-11-22]

- Adopt application startup hook for cone.ugm only setting auth implementation
  if explicitely defined.
  [rnix, 2011-11-21]


0.9
---

- make it work
  [rnix, chaoflow]
