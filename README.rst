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

Summary of the test coverage report::

    lines   cov%   module
       19   100%   node.ext.ugm.__init__
       96   100%   node.ext.ugm._api
      469    99%   node.ext.ugm.file
       41   100%   node.ext.ugm.interfaces
       16   100%   node.ext.ugm.tests


Contributors
============

- Robert Niederreiter <rnix [at] squarewave [dot] at>

- Florian Friesdorf <flo [at] chaoflow [dot] net>


Changes
=======

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
