node.ext.ugm
============

::

    >>> from plumber import plumber
    >>> from node.parts import (
    ...     NodeChildValidate,
    ...     Nodespaces,
    ...     Adopt,
    ...     Attributes,
    ...     DefaultInit,
    ...     Nodify,
    ...     DictStorage,
    ...     OdictStorage,
    ... )

Abstract principal part::

    >>> from node.ext.ugm.interfaces import IPrincipal
    >>> from node.ext.ugm import Principal
    >>> class PrincipalNode(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = (
    ...         NodeChildValidate,
    ...         Nodespaces,
    ...         Adopt,
    ...         Attributes,
    ...         DefaultInit,
    ...         Nodify,
    ...         Principal,
    ...         DictStorage,
    ...     )
    
    >>> principal = PrincipalNode(name='someprincipal')
    >>> principal
    <PrincipalNode object 'someprincipal' at ...>
    
    >>> IPrincipal.providedBy(principal)
    True
    
    >>> [key for key in principal]
    []

``add_role``, ``remove_role``, ``roles`` and ``__call__`` is not implemented 
on abstract principal::

    >>> principal.add_role('role')
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Principal`` does not implement ``add_role``
    
    >>> principal.remove_role('role')
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Principal`` does not implement ``remove_role``
    
    >>> principal.roles
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Principal`` does not implement ``roles``
    
    >>> principal()
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Principal`` does not implement ``__call__``

Abstract user part::
    
    >>> from node.ext.ugm.interfaces import IUser
    >>> from node.ext.ugm import User
    >>> class UserNode(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = (
    ...         NodeChildValidate,
    ...         Nodespaces,
    ...         Adopt,
    ...         Attributes,
    ...         DefaultInit,
    ...         Nodify,
    ...         User,
    ...         DictStorage,
    ...     )
    
    >>> user = UserNode(name='someuser')
    >>> user
    <UserNode object 'someuser' at ...>
    
    >>> IUser.providedBy(user)
    True
    
    >>> user.login
    'someuser'
    
    >>> user.attrs['login'] = 'foo@bar.baz'
    >>> user.login
    'foo@bar.baz'
    
    >>> user['foo']
    Traceback (most recent call last):
      ...
    NotImplementedError: User does not implement ``__getitem__``
    
    >>> user['foo'] = UserNode()
    Traceback (most recent call last):
      ...
    NotImplementedError: User does not implement ``__setitem__``
    
    >>> del user['foo']
    Traceback (most recent call last):
      ...
    NotImplementedError: User does not implement ``__delitem__``
    
    >>> [x for x in user]
    []

``authenticate`` and ``passwd`` gets delegated to parent. Fails since User is
not contained in Users container::

    >>> user.authenticate('secret')
    Traceback (most recent call last):
      ...
    AttributeError: 'NoneType' object has no attribute 'authenticate'

    >>> user.passwd('old', 'new')
    Traceback (most recent call last):
      ...
    AttributeError: 'NoneType' object has no attribute 'passwd'

Also ``groups`` is not implemented in abstract base part::

    >>> user.groups
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``User`` does not implement ``groups``

Abstract group part::
    
    >>> from node.ext.ugm.interfaces import IGroup
    >>> from node.ext.ugm import Group
    >>> class GroupNode(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = (
    ...         NodeChildValidate,
    ...         Nodespaces,
    ...         Adopt,
    ...         Attributes,
    ...         DefaultInit,
    ...         Nodify,
    ...         Group,
    ...         DictStorage,
    ...     )
    
    >>> group = GroupNode(name='somegroup')
    >>> group
    <GroupNode object 'somegroup' at ...>
    
    >>> IGroup.providedBy(group)
    True

``users`` and ``member_ids`` is not implemented in abstract base part::

    >>> group.users
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Group`` does not implement ``users``
    
    >>> group.member_ids
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Group`` does not implement ``member_ids``
    
    >>> group.add('foo')
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Group`` does not implement ``add``
    
    >>> group['foo'] = GroupNode()
    Traceback (most recent call last):
      ...
    NotImplementedError: Group does not implement ``__setitem__``

Abstract principals part::

    >>> from node.ext.ugm.interfaces import IPrincipals
    >>> from node.ext.ugm import Principals
    >>> class PrincipalsNode(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = (
    ...         NodeChildValidate,
    ...         Nodespaces,
    ...         Adopt,
    ...         Attributes,
    ...         DefaultInit,
    ...         Nodify,
    ...         Principals,
    ...         OdictStorage,
    ...     )
    
    >>> principals = PrincipalsNode(name='principals')
    >>> principals
    <PrincipalsNode object 'principals' at ...>
    
    >>> IPrincipals.providedBy(principals)
    True
    
    >>> principals.ids
    []

``search`` ,``create`` and ``__call__`` are not implemented in abstract base 
part::

    >>> principals.search()
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Principals`` does not implement ``search``
    
    >>> principals.create('foo')
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Principals`` does not implement ``create``
    
    >>> principals()
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Principals`` does not implement ``__call__``

    
Abstract users part::

    >>> from node.ext.ugm.interfaces import IUsers
    >>> from node.ext.ugm import Users
    >>> class UsersNode(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = (
    ...         NodeChildValidate,
    ...         Nodespaces,
    ...         Adopt,
    ...         Attributes,
    ...         DefaultInit,
    ...         Nodify,
    ...         Users,
    ...         OdictStorage,
    ...     )
    
    >>> users = UsersNode(name='users')
    >>> users
    <UsersNode object 'users' at ...>
    
    >>> IUsers.providedBy(users)
    True

Add previously created user::

    >>> users[user.name] = user
    >>> users.printtree()
    <class 'UsersNode'>: users
      <class 'UserNode'>: someuser
    
    >>> users.ids
    ['someuser']

Abstract users part does not implement ``authenticate`` and ``passwd``::

    >>> user.authenticate('secret')
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Users`` does not implement ``authenticate``

    >>> user.passwd('old', 'new')
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Users`` does not implement ``passwd``

Abstract groups part::

    >>> from node.ext.ugm.interfaces import IGroups
    >>> from node.ext.ugm import Groups
    >>> class GroupsNode(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = (
    ...         NodeChildValidate,
    ...         Nodespaces,
    ...         Adopt,
    ...         Attributes,
    ...         DefaultInit,
    ...         Nodify,
    ...         Groups,
    ...         OdictStorage,
    ...     )
    
    >>> groups = GroupsNode(name='groups')
    >>> groups
    <GroupsNode object 'groups' at ...>
    
    >>> IGroups.providedBy(groups)
    True

Abstract ugm part::

    >>> from node.ext.ugm.interfaces import IUgm
    >>> from node.ext.ugm import Ugm
    >>> class UgmNode(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = (
    ...         NodeChildValidate,
    ...         Nodespaces,
    ...         Adopt,
    ...         Attributes,
    ...         Nodify,
    ...         Ugm,
    ...         OdictStorage,
    ...     )
    ...     def __init__(self, name, users, groups):
    ...         self.__name__ = name
    ...         self['users'] = users
    ...         self['groups'] = groups
    ...     @property
    ...     def users(self):
    ...         return self['users']
    ...     @property
    ...     def groups(self):
    ...         return self['groups']
    ...     @property
    ...     def roles_storage(self):
    ...         return lambda: None
    
    >>> ugm = UgmNode('ugm', users, groups)
    >>> ugm
    <UgmNode object 'ugm' at ...>
    
    >>> IUgm.providedBy(ugm)
    True
    
    >>> ugm.users
    <UsersNode object 'users' at ...>
    
    >>> ugm.groups
    <GroupsNode object 'groups' at ...>
    
    >>> ugm.roles_storage
    <function <lambda> at ...>
    
Abstract ugm part does not implement ``add_role``, ``remove_role``, ``roles``
and ``__call__``::

    >>> ugm.add_role('role', user)
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Ugm`` does not implement ``add_role``
    
    >>> ugm.remove_role('role', user)
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Ugm`` does not implement ``remove_role``
    
    >>> ugm.roles(user)
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Ugm`` does not implement ``roles``
    
    >>> ugm()
    Traceback (most recent call last):
      ...
    NotImplementedError: Abstract ``Ugm`` does not implement ``__call__``
