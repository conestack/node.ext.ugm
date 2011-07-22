User and group management
=========================

``node.ext.ugm`` provides an API for node based managing of users and groups.

See ``node.ext.ugm.interfaces`` for a description of the API.

A file based default implementation can be found at ``node.ext.ugm.file``.

Base plumbing parts for writing a UGM implementations can be found at
``node.ext.ugm._api``.

For more information on nodes see `node <http://pypi.python.org/pypi/node>`_
package.

For more information on plumbing see
`plumber <http://pypi.python.org/pypi/plumber>`_ package.


TODO
====

- more concrete interface for ``node.ext.ugm.interfaces.IPrincipals.search``


Contributors
============

- Robert Niederreiter <rnix [at] squarewave [dot] at>
- Florian Friesdorf <flo [at] chaoflow [dot] net>>


Changes
=======

0.9dev  
------

- make it work
  [rnix, chaoflow]
