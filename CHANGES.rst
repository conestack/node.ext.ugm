Changes
=======

0.9.13 (2021-11-08)
-------------------

- Rename deprecated ``FileStorage.allow_non_node_childs`` to
  ``allow_non_node_children``
  [rnix]


0.9.12 (2020-07-09)
-------------------

- ``node.ext.ugm.file.GroupBehavior.add`` properly raises ``KeyError`` if given
  user not exists.
  [rnix]

- Also call parent in ``node.ext.ugm.file.UserBehavior.__call__`` and
  ``node.ext.ugm.file.GroupBehavior.__call__`` if not called from parent.
  [rnix]

- ``node.ext.ugm.file.FileStorage.invalidate`` gets set with
  ``plumber.override`` instead of ``plumber.default`` to work on
  ``node.ext.ugm.file.Users`` and ``node.ext.ugm.file.Groups``.
  [rnix]

- ``node.ext.ugm.file.FileStorage`` values can be ``node.utils.UNSET``.
  [rnix]


0.9.11 (2020-05-28)
-------------------

- Implement ``invalidate`` on ``node.ext.ugm.file.Ugm``.
  [rnix, 2020-05-16]

- ``node.ext.ugm.interfaces.IUgm`` inherits from
  ``node.interfaces.IInvalidate`` now.
  [rnix, 2020-05-16]

- Describe behavior of ``__getitem__``, ``__delitem__`` and ``__iter__`` on
  ``IGroup`` interface.
  [rnix, 2020-05-11]

- Fix file based ``GroupBehavior.__getitem__`` to properly raise ``KeyError``
  when accessing user which is no member of group.
  [rnix, 2020-05-11]

- Make clear on ``User`` and ``Group`` behaviors which not impelented functions
  are abstract and which are not supported.
  [rnix, 2020-05-11]


0.9.10 (2019-11-07)
-------------------

- Also derive ``IPrincipals`` interface from ``node.interfaces.IInvalidate``.
  Implement ``invalidate`` function on ``FileStorage``.
  [rnix, 2019-06-30]

- Persist users file on password change.
  [rnix, 2019-06-30]

- Add ``UserAttributes`` and ``GroupAttributes`` classes deriving from
  ``FileAttributes`` and handle reserved attributes expected by ``cone.ugm``
  there. This might change in future.
  [rnix, 2019-06-27]

- File based principals support binary attributes now.
  [rnix, 2019-06-26]

- Return all principals in file based UGM imlementation if no search criteria
  given.
  [rnix, 2019-06-26]

- Remove superfluous ``configure.zcml`` file.
  [rnix, 2019-04-13]

- Remove ``cone.app`` main hook for initializing file based UGM implementation.
  This is handled in ``cone.app`` itself as of version 1.0
  [rnix, 2019-03-28]


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
