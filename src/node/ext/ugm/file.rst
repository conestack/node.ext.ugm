Default UGM implementation
==========================

Create a test environment::

    >>> import os
    >>> import tempfile
    >>> tempdir = tempfile.mkdtemp()

File storage part::

    >>> from plumber import plumber
    >>> from node.parts import (
    ...     NodeChildValidate,
    ...     Nodespaces,
    ...     Adopt,
    ...     Attributes,
    ...     DefaultInit,
    ...     Nodify,
    ... )
    >>> from node.ext.ugm.file import FileStorage
    
    >>> class FileStorageNode(object):
    ...     __metaclass__ = plumber
    ...     __plumbing__ = (
    ...         NodeChildValidate,
    ...         Nodespaces,
    ...         Adopt,
    ...         Attributes,
    ...         DefaultInit,
    ...         Nodify,
    ...         FileStorage,
    ...     )
    ...     def __init__(self, file_path):
    ...         self.__name__ = None
    ...         self.__parent__ = None
    ...         self.file_path = file_path
    
    >>> file_path = os.path.join(tempdir, 'filestorage')
    >>> file_path
    '/.../filestorage'
    
    >>> fsn = FileStorageNode(file_path)
    >>> fsn
    <FileStorageNode object 'None' at ...>
    
    >>> list(fsn.__iter__())
    []
    
    >>> fsn['inexistent']
    Traceback (most recent call last):
      ...
    KeyError: 'inexistent'
    
    >>> del fsn['inexistent']
    Traceback (most recent call last):
      ...
    KeyError: 'inexistent'
    
    >>> fsn['foo'] = 'foo'
    >>> fsn.keys()
    ['foo']
    
    >>> fsn['foo']
    'foo'
    
    >>> fsn['bar'] = 'bar'
    
File not written yet::

    >>> open(file_path)
    Traceback (most recent call last):
      ...
    IOError: [Errno 2] No such file or directory: '/.../filestorage'
    
    >>> fsn()
    >>> with open(file_path) as file:
    ...     for line in file:
    ...         print line
    foo:foo
    <BLANKLINE>
    bar:bar
    <BLANKLINE>

Recreate:: 

    >>> fsn = FileStorageNode(file_path)
    >>> fsn.keys()
    [u'foo', u'bar']
    
    >>> fsn.values()
    [u'foo', u'bar']

Test unicode::

    >>> fsn[u'\xe4\xf6\xfc'] = u'\xe4\xf6\xfc'
    >>> fsn()
    
    >>> fsn = FileStorageNode(file_path)
    >>> fsn.items()
    [(u'foo', u'foo'), (u'bar', u'bar'), (u'\xe4\xf6\xfc', u'\xe4\xf6\xfc')]

Create principal data directory::

    >>> datadir = os.path.join(tempdir, 'principal_data')
    >>> os.mkdir(datadir)

Ugm root object::

    >>> from node.ext.ugm.file import Ugm
    >>> users_file = os.path.join(tempdir, 'users')
    >>> groups_file = os.path.join(tempdir, 'groups')
    >>> roles_file = os.path.join(tempdir, 'roles')
    >>> ugm = Ugm(name='ugm',
    ...           users_file=users_file,
    ...           groups_file=groups_file,
    ...           roles_file=roles_file,
    ...           data_directory=datadir)
    
    >>> ugm
    <Ugm object 'ugm' at ...>
    
    >>> ugm.users
    <Users object 'users' at ...>
    
    >>> ugm.groups
    <Groups object 'groups' at ...>
    
    >>> ugm.attrs
    <FileAttributes object '__attrs__' at ...>
    
    >>> ugm.roles_storage
    <FileAttributes object '__attrs__' at ...>
    
    >>> ugm.attrs is ugm.roles_storage
    True
    
    >>> del ugm['users']
    Traceback (most recent call last):
      ...
    NotImplementedError: Operation forbidden on this node.
    
    >>> ugm['inexistent'] = ugm.users
    Traceback (most recent call last):
      ...
    KeyError: 'inexistent'

Nothing created yet::

    >>> sorted(os.listdir(tempdir))
    ['filestorage', 'principal_data']
    
Calling UGM persists::

    >>> ugm()
    >>> sorted(os.listdir(tempdir))
    ['filestorage', 'groups', 'principal_data', 'roles', 'users']

Add new User::

    >>> user = ugm.users.create('max',
    ...                         fullname='Max Mustermann',
    ...                         email='foo@bar.com')
    >>> user
    <User object 'max' at ...>
    
    >>> ugm.printtree()
    <class 'node.ext.ugm.file.Ugm'>: ugm
      <class 'node.ext.ugm.file.Users'>: users
        <class 'node.ext.ugm.file.User'>: max
      <class 'node.ext.ugm.file.Groups'>: groups

Nothing written yet::

    >>> file = open(ugm.users.file_path)
    >>> file.readlines()
    []
    
    >>> file.close()
    
    >>> user.attrs.file_path
    '/.../principal_data/users/max'
    
    >>> file = open(user.attrs.file_path)
    Traceback (most recent call last):
      ...
    IOError: [Errno 2] No such file or directory: '/.../users/max'
    
Persist and read related files again::

    >>> ugm()
    >>> file = open(ugm.users.file_path)
    >>> file.readlines()
    ['max:\n']
    
    >>> file.close()
    >>> file = open(user.attrs.file_path)
    >>> file.readlines()
    ['fullname:Max Mustermann\n', 
    'email:foo@bar.com\n']
    
    >>> file.close()

Authentication is prohibited for users without a password::

    >>> ugm.users.authenticate('max', 'secret')
    False

Set Password for new User::

    >>> ugm.users.passwd('max', '', 'secret')
    >>> ugm()
    >>> file = open(ugm.users.file_path)
    >>> file.readlines()
    ['max:/\xfeqwgR8ohuY5M\n']
    
    >>> file.close()

Password for inextistent user::

    >>> ugm.users.passwd('sepp', '', 'secret')
    Traceback (most recent call last):
      ...
    ValueError: User with id 'sepp' does not exist.

Password with wrong oldpw::

    >>> ugm.users.passwd('max', 'wrong', 'new')
    Traceback (most recent call last):
      ...
    ValueError: Old password does not match.

Set new password for max::

    >>> ugm.users.passwd('max', 'secret', 'secret1')
    >>> ugm()
    >>> file = open(ugm.users.file_path)
    >>> file.readlines()
    ['max:/\xfe3434cetAdTc\n']
    
    >>> file.close()

Authentication::

    >>> ugm.users.authenticate('inexistent', 'secret')
    False
    
    >>> ugm.users.authenticate('max', 'secret')
    False
    
    >>> ugm.users.authenticate('max', 'secret1')
    True

Add another user::

    >>> user = ugm.users.create('sepp',
    ...                         fullname='Sepp Mustermann',
    ...                         email='baz@bar.com')
    >>> ugm.users.passwd('sepp', '', 'secret')
    >>> ugm()
    
    >>> ugm.printtree()
    <class 'node.ext.ugm.file.Ugm'>: ugm
      <class 'node.ext.ugm.file.Users'>: users
        <class 'node.ext.ugm.file.User'>: max
        <class 'node.ext.ugm.file.User'>: sepp
      <class 'node.ext.ugm.file.Groups'>: groups
    
    >>> file = open(ugm.users.file_path)
    >>> file.readlines()
    ['max:/\xfe3434cetAdTc\n', 
    'sepp:\xec\xb8Go8sxwk1E6g\n']
    
    >>> file.close()

``__setitem__`` on user is prohibited::

    >>> ugm.users['max']['foo'] = user
    Traceback (most recent call last):
      ...
    NotImplementedError: User does not implement ``__setitem__``

Add new Group::

    >>> group = ugm.groups.create('group1', description='Group 1 Description')
    >>> group
    <Group object 'group1' at ...>
    
    >>> ugm.printtree()
    <class 'node.ext.ugm.file.Ugm'>: ugm
      <class 'node.ext.ugm.file.Users'>: users
        <class 'node.ext.ugm.file.User'>: max
        <class 'node.ext.ugm.file.User'>: sepp
      <class 'node.ext.ugm.file.Groups'>: groups
        <class 'node.ext.ugm.file.Group'>: group1

Nothing written yet::

    >>> file = open(ugm.groups.file_path)
    >>> file.readlines()
    []
    
    >>> file.close()
    
    >>> group.attrs.file_path
    '/.../principal_data/groups/group1'
    
    >>> file = open(group.attrs.file_path)
    Traceback (most recent call last):
      ...
    IOError: [Errno 2] No such file or directory: '/.../groups/group1'

Persist and read related files again::

    >>> ugm()
    >>> file = open(ugm.groups.file_path)
    >>> file.readlines()
    ['group1:\n']
    
    >>> file.close()
    >>> file = open(group.attrs.file_path)
    >>> file.readlines()
    ['description:Group 1 Description\n']
    
    >>> file.close()

No members yet::

    >>> group.member_ids
    []

Setitem is forbidden on a group::

    >>> group['foo'] = ugm.users['max']
    Traceback (most recent call last):
      ...
    NotImplementedError: Group does not implement ``__setitem__``

A user is added to a group via ``add``::

    >>> id = ugm.users['max'].name
    >>> id
    'max'
    
    >>> group.add(id)
    >>> group.member_ids
    ['max']
    
    >>> group.users
    [<User object 'max' at ...>]
    
    >>> group['max']
    <User object 'max' at ...>

Nothing written yet::

    >>> file = open(ugm.groups.file_path)
    >>> file.readlines()
    ['group1:\n']
    
    >>> file.close()
    
    >>> ugm()
    >>> file = open(ugm.groups.file_path)
    >>> file.readlines()
    ['group1:max\n']
    
    >>> file.close()

Note, parent of returned user is users object, not group::

    >>> group['max'].path
    ['ugm', 'users', 'max']

Add another Group and add members::

    >>> group = ugm.groups.create('group2', description='Group 2 Description')
    >>> group
    <Group object 'group2' at ...>
    
    >>> group.add('max')
    >>> group.add('sepp')
    
    >>> ugm.printtree()
    <class 'node.ext.ugm.file.Ugm'>: ugm
      <class 'node.ext.ugm.file.Users'>: users
        <class 'node.ext.ugm.file.User'>: max
        <class 'node.ext.ugm.file.User'>: sepp
      <class 'node.ext.ugm.file.Groups'>: groups
        <class 'node.ext.ugm.file.Group'>: group1
          <class 'node.ext.ugm.file.User'>: max
        <class 'node.ext.ugm.file.Group'>: group2
          <class 'node.ext.ugm.file.User'>: max
          <class 'node.ext.ugm.file.User'>: sepp
    
    >>> file = open(ugm.groups.file_path)
    >>> file.readlines()
    ['group1:max\n']
    
    >>> file.close()
    
    >>> ugm()
    >>> file = open(ugm.groups.file_path)
    >>> file.readlines()
    ['group1:max\n', 
    'group2:max,sepp\n']
    
    >>> file.close()

``groups`` attribute on user::

    >>> max = ugm.users['max']
    >>> max.groups
    [<Group object 'group1' at ...>, 
    <Group object 'group2' at ...>]
    
    >>> sepp = ugm.users['sepp']
    >>> sepp.groups
    [<Group object 'group2' at ...>]

``search`` function::

    >>> groups = ugm.groups
    >>> groups.search(id='group1')
    [{'description': 'Group 1 Description', 'id': 'group1'}]
    
    >>> groups.search(description='group 1')
    [{'description': 'Group 1 Description', 'id': 'group1'}]
    
    >>> groups.search(description='group')
    [{'description': 'Group 1 Description', 'id': 'group1'}, 
    {'description': 'Group 2 Description', 'id': 'group2'}]
    
    >>> users = ugm.users
    >>> users.search(id='max')
    [{'fullname': 'Max Mustermann', 'email': 'foo@bar.com', 'id': 'max'}]
    
    >>> users.search(email='baz')
    [{'fullname': 'Sepp Mustermann', 'email': 'baz@bar.com', 'id': 'sepp'}]

Delete user from group::

    >>> ugm.groups.printtree()
    <class 'node.ext.ugm.file.Groups'>: groups
      <class 'node.ext.ugm.file.Group'>: group1
        <class 'node.ext.ugm.file.User'>: max
      <class 'node.ext.ugm.file.Group'>: group2
        <class 'node.ext.ugm.file.User'>: max
        <class 'node.ext.ugm.file.User'>: sepp
    
    >>> del ugm.groups['group2']['inexistent']
    Traceback (most recent call last):
      ...
    KeyError: 'inexistent'
    
    >>> del ugm.groups['group2']['max']
    >>> ugm.groups.printtree()
    <class 'node.ext.ugm.file.Groups'>: groups
      <class 'node.ext.ugm.file.Group'>: group1
        <class 'node.ext.ugm.file.User'>: max
      <class 'node.ext.ugm.file.Group'>: group2
        <class 'node.ext.ugm.file.User'>: sepp

Not persisted yet::

    >>> file = open(ugm.groups.file_path)
    >>> file.readlines()
    ['group1:max\n', 
    'group2:max,sepp\n']
    
    >>> file.close()

Call tree and check result::

    >>> ugm()
    >>> file = open(ugm.groups.file_path)
    >>> file.readlines()
    ['group1:max\n', 
    'group2:sepp\n']
    
    >>> file.close()

Recreate ugm object::

    >>> ugm = Ugm(name='ugm',
    ...           users_file=users_file,
    ...           groups_file=groups_file,
    ...           roles_file=roles_file,
    ...           data_directory=datadir)

Users ``__getitem__``::

    >>> ugm.users['inexistent']
    Traceback (most recent call last):
      ...
    KeyError: 'inexistent'
    
    >>> ugm.users['max']
    <User object 'max' at ...>

Groups ``__getitem__``::

    >>> ugm.groups['inexistent']
    Traceback (most recent call last):
      ...
    KeyError: 'inexistent'
    
    >>> ugm.groups['group1']
    <Group object 'group1' at ...>

``printtree`` of alredy initialized ugm instance::

    >>> ugm = Ugm(name='ugm',
    ...           users_file=users_file,
    ...           groups_file=groups_file,
    ...           roles_file=roles_file,
    ...           data_directory=datadir)
    >>> ugm.printtree()
    <class 'node.ext.ugm.file.Ugm'>: ugm
      <class 'node.ext.ugm.file.Users'>: users
        <class 'node.ext.ugm.file.User'>: max
        <class 'node.ext.ugm.file.User'>: sepp
      <class 'node.ext.ugm.file.Groups'>: groups
        <class 'node.ext.ugm.file.Group'>: group1
          <class 'node.ext.ugm.file.User'>: max
        <class 'node.ext.ugm.file.Group'>: group2
          <class 'node.ext.ugm.file.User'>: sepp

Role Management for User.

No roles yet::

    >>> user = ugm.users['max']
    >>> user.roles
    []

Add role via User object::

    >>> user.add_role('manager')
    >>> user.roles
    ['manager']

Add same role twice fails::

    >>> user.add_role('manager')
    Traceback (most recent call last):
      ...
    ValueError: Principal already has role 'manager'

Not written yet::

    >>> file = open(ugm.roles_file)
    >>> file.readlines()
    []

    >>> file.close()

After ``__call__`` roles are persisted::

    >>> user()
    >>> file = open(ugm.roles_file)
    >>> file.readlines()
    ['max::manager\n']
    
    >>> file.close()

Add role for User via Ugm object::

    >>> ugm.add_role('supervisor', user)
    >>> user.roles
    ['manager', 'supervisor']
    
    >>> ugm.roles(user) == user.roles
    True

Call and check result::

    >>> ugm()
    >>> file = open(ugm.roles_file)
    >>> file.readlines()
    ['max::manager,supervisor\n']
    
    >>> file.close()

Remove User role::

    >>> user.remove_role('supervisor')
    >>> user.roles
    ['manager']

Remove inexistent role fails::

    >>> user.remove_role('supervisor')
    Traceback (most recent call last):
      ...
    ValueError: Principal does not has role 'supervisor'

Call persists::

    >>> user()
    >>> file = open(ugm.roles_file)
    >>> file.readlines()
    ['max::manager\n']
    
    >>> file.close()

Role Management for Group.

No roles yet::

    >>> group = ugm.groups['group1']
    >>> group.roles
    []

Add role via Group object::

    >>> group.add_role('authenticated')
    >>> group.roles
    ['authenticated']

Add same role twice fails::

    >>> group.add_role('authenticated')
    Traceback (most recent call last):
      ...
    ValueError: Principal already has role 'authenticated'

Group role not written yet::

    >>> file = open(ugm.roles_file)
    >>> file.readlines()
    ['max::manager\n']
    
    >>> file.close()

After ``__call__`` roles are persisted::

    >>> group()
    >>> file = open(ugm.roles_file)
    >>> file.readlines()
    ['max::manager\n', 
    'group:group1::authenticated\n']
    
    >>> file.close()

Add role for Group via Ugm object::

    >>> ugm.add_role('editor', group)
    >>> group.roles
    ['authenticated', 'editor']
    
    >>> ugm.roles(group) == group.roles
    True

Call and check result::

    >>> ugm()
    >>> file = open(ugm.roles_file)
    >>> file.readlines()
    ['max::manager\n', 
    'group:group1::authenticated,editor\n']
    
    >>> file.close()

Remove Group role::

    >>> group.remove_role('editor')
    >>> group.roles
    ['authenticated']

Remove inexistent role fails::

    >>> group.remove_role('editor')
    Traceback (most recent call last):
      ...
    ValueError: Principal does not has role 'editor'

Call persists::
    
    >>> group()
    >>> file = open(ugm.roles_file)
    >>> file.readlines()
    ['max::manager\n', 
    'group:group1::authenticated\n']
    
    >>> file.close()

Users ``__delitem__``::

    >>> users = ugm.users
    >>> del users['max']
    >>> ugm.printtree()
    <class 'node.ext.ugm.file.Ugm'>: ugm
      <class 'node.ext.ugm.file.Users'>: users
        <class 'node.ext.ugm.file.User'>: sepp
      <class 'node.ext.ugm.file.Groups'>: groups
        <class 'node.ext.ugm.file.Group'>: group1
        <class 'node.ext.ugm.file.Group'>: group2
          <class 'node.ext.ugm.file.User'>: sepp
    
    >>> users()
    >>> file = open(ugm.users.file_path)
    >>> file.readlines()
    ['sepp:\xec\xb8Go8sxwk1E6g\n']
    
    >>> file.close()

Roles for user are deleted as well::

    >>> file = open(ugm.roles_file)
    >>> file.readlines()
    ['group:group1::authenticated\n']
    
    >>> file.close()

Groups ``__delitem__``::

    >>> groups = ugm.groups
    >>> del groups['group1']
    >>> ugm.printtree()
    <class 'node.ext.ugm.file.Ugm'>: ugm
      <class 'node.ext.ugm.file.Users'>: users
        <class 'node.ext.ugm.file.User'>: sepp
      <class 'node.ext.ugm.file.Groups'>: groups
        <class 'node.ext.ugm.file.Group'>: group2
          <class 'node.ext.ugm.file.User'>: sepp
    
    >>> groups()
    >>> file = open(ugm.groups.file_path)
    >>> file.readlines()
    ['group2:sepp\n']
    
    >>> file.close()

Roles for group are deleted as well::

    >>> file = open(ugm.roles_file)
    >>> file.readlines()
    []
    
    >>> file.close()

Cleanup test environment::
  
    >>> import shutil
    >>> shutil.rmtree(tempdir)