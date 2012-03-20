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


Contributors
============

- Robert Niederreiter <rnix [at] squarewave [dot] at>
- Florian Friesdorf <flo [at] chaoflow [dot] net>


Changes
=======

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
