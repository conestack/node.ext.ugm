from __future__ import print_function
from node.behaviors import Adopt
from node.behaviors import Attributes
from node.behaviors import DefaultInit
from node.behaviors import NodeChildValidate
from node.behaviors import Nodespaces
from node.behaviors import Nodify
from node.ext.ugm.file import FileStorage
from node.ext.ugm.file import Ugm
from node.tests import NodeTestCase
from plumber import plumbing
import os
import shutil
import tempfile

###############################################################################
# Mock objects
###############################################################################

@plumbing(
    NodeChildValidate,
    Nodespaces,
    Adopt,
    Attributes,
    DefaultInit,
    Nodify,
    FileStorage)
class FileStorageNode(object):
    """File storage.
    """

    def __init__(self, file_path):
        self.__name__ = None
        self.__parent__ = None
        self.file_path = file_path
        self._storage_data = None


###############################################################################
# Tests
###############################################################################

class TestFile(NodeTestCase):
    # Default UGM implementation

    @classmethod
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    @classmethod
    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def _create_ugm(self):
        # Create principal data directory
        datadir = os.path.join(self.tempdir, 'principal_data')
        os.mkdir(datadir)
        # Return Ugm root object
        return Ugm(
            name='ugm',
            users_file=os.path.join(self.tempdir, 'users'),
            groups_file=os.path.join(self.tempdir, 'groups'),
            roles_file=os.path.join(self.tempdir, 'roles'),
            data_directory=datadir
        )

    def test_file_storage(self):
        file_path = os.path.join(self.tempdir, 'filestorage')
        fsn = FileStorageNode(file_path)

        expected = '<FileStorageNode object \'None\' at '
        self.assertTrue(str(fsn).startswith(expected))
        self.assertEqual(list(fsn.__iter__()), [])

        # __setitem__
        fsn['foo'] = 'foo'
        fsn['bar'] = 'bar'
        fsn['baz'] = 'baz'
        fsn['none'] = None

        # __getitem__
        def __getitem__fails():
            fsn['inexistent']
        err = self.expect_error(KeyError, __getitem__fails)
        self.assertEqual(str(err), '\'inexistent\'')
        self.assertEqual(fsn['foo'], 'foo')
        self.assertEqual(fsn['none'], None)

        # __iter__
        self.assertEqual(list(fsn.keys()), ['foo', 'bar', 'baz', 'none'])

        # __delitem__
        def __delitem__fails():
            del fsn['inexistent']
        err = self.expect_error(KeyError, __delitem__fails)
        self.assertEqual(str(err), '\'inexistent\'')
        del fsn['baz']

        # File not written yet
        err = self.expect_error(IOError, open, file_path)
        self.check_output("""\
        [Errno 2] No such file or directory: '/.../filestorage'
        """, str(err))

        # Persist and check written file
        fsn()
        with open(file_path) as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            'foo:foo\n',
            'bar:bar\n',
            'none:\n'
        ])

        # Recreate
        fsn = FileStorageNode(file_path)
        self.assertEqual(list(fsn.keys()), [u'foo', u'bar', u'none'])
        self.assertEqual(list(fsn.values()), [u'foo', u'bar', u''])

        # Test unicode
        fsn[u'\xe4\xf6\xfc'] = u'\xe4\xf6\xfc'
        fsn()
        fsn = FileStorageNode(file_path)
        self.assertEqual(sorted(list(fsn.items())), [
            (u'bar', u'bar'),
            (u'foo', u'foo'),
            (u'none', u''),
            (u'\xe4\xf6\xfc', u'\xe4\xf6\xfc')
        ])

    def test_ugm(self):
        ugm = self._create_ugm()

        expected = '<Ugm object \'ugm\' at '
        self.assertTrue(str(ugm).startswith(expected))

        expected = '<Users object \'users\' at '
        self.assertTrue(str(ugm.users).startswith(expected))

        expected = '<Groups object \'groups\' at '
        self.assertTrue(str(ugm.groups).startswith(expected))

        expected = '<FileAttributes object \'__attrs__\' at'
        self.assertTrue(str(ugm.attrs).startswith(expected))
        self.assertTrue(str(ugm.roles_storage).startswith(expected))
        self.assertTrue(ugm.attrs is ugm.roles_storage)

        def __setitem__fails():
            ugm['inexistent'] = ugm.users
        err = self.expect_error(KeyError, __setitem__fails)
        self.assertEqual(str(err), '\'inexistent\'')

        def __delitem__fails():
            del ugm['users']
        err = self.expect_error(NotImplementedError, __delitem__fails)
        expected = 'Operation forbidden on this node.'
        self.assertEqual(str(err), expected)

        # Nothing created yet
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['principal_data']
        )
        # Calling UGM persists
        ugm()
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['groups', 'principal_data', 'roles', 'users']
        )

    def test_user(self):
        ugm = self._create_ugm()
        ugm()

        # Add new User
        user = ugm.users.create('max', fullname='Max', email='foo@bar.com')
        expected = '<User object \'max\' at '
        self.assertTrue(str(user).startswith(expected))
        self.assertEqual(ugm.treerepr(), (
            '<class \'node.ext.ugm.file.Ugm\'>: ugm\n'
            '  <class \'node.ext.ugm.file.Users\'>: users\n'
            '    <class \'node.ext.ugm.file.User\'>: max\n'
            '  <class \'node.ext.ugm.file.Groups\'>: groups\n'
        ))

        # Nothing written yet
        with open(ugm.users.file_path) as f:
            lines = f.readlines()
        self.assertEqual(lines, [])

        self.check_output("""\
        /.../principal_data/users/max
        """, user.attrs.file_path)

        err = self.expect_error(IOError, open, user.attrs.file_path)
        self.check_output("""\
        [Errno 2] No such file or directory: '/.../users/max'
        """, str(err))

        # Persist and read related files again
        ugm()
        with open(ugm.users.file_path) as f:
            lines = f.readlines()
        self.assertEqual(lines, ['max:\n'])

        with open(user.attrs.file_path) as f:
            lines = f.readlines()
        self.assertEqual(sorted(lines), [
            'email:foo@bar.com\n',
            'fullname:Max\n'
        ])

        # Authentication is prohibited for users without a password
        self.assertFalse(ugm.users.authenticate('max', 'secret'))

        # Set Password for new User
        ugm.users.passwd('max', None, 'secret')
        ugm()
        with open(ugm.users.file_path) as f:
            lines = f.readlines()
        self.check_output("""\
        ['max:...\\n']
        """, str(lines))

        # Password for inextistent user
        err = self.expect_error(ValueError, ugm.users.passwd,
                                'sepp', None, 'secret')
        expected = 'User with id \'sepp\' does not exist.'
        self.assertEqual(str(err), expected)

        # Password with wrong oldpw
        err = self.expect_error(ValueError, ugm.users.passwd,
                                'max', 'wrong', 'new')
        expected = 'Old password does not match.'
        self.assertEqual(str(err), expected)

        # Set new password for max
        ugm.users.passwd('max', 'secret', 'secret1')
        ugm()
        with open(ugm.users.file_path) as f:
            lines = f.readlines()
        self.check_output("""\
        ['max:...\\n']
        """, str(lines))

        # Authentication
        self.assertFalse(ugm.users.authenticate('inexistent', 'secret'))
        self.assertFalse(ugm.users.authenticate('max', 'secret'))
        self.assertTrue(ugm.users.authenticate('max', 'secret1'))

        # Add another user
        user = ugm.users.create('sepp', fullname='Sepp', email='baz@bar.com')
        ugm.users.passwd('sepp', None, 'secret')
        ugm()
        self.assertEqual(ugm.treerepr(), (
            '<class \'node.ext.ugm.file.Ugm\'>: ugm\n'
            '  <class \'node.ext.ugm.file.Users\'>: users\n'
            '    <class \'node.ext.ugm.file.User\'>: max\n'
            '    <class \'node.ext.ugm.file.User\'>: sepp\n'
            '  <class \'node.ext.ugm.file.Groups\'>: groups\n'
        ))
        with open(ugm.users.file_path) as f:
            lines = f.readlines()
        self.check_output("""\
        ['max:...\\n',
        'sepp:...\\n']
        """, str(lines))

        # ``__setitem__`` on user is prohibited
        def __setitem__fails():
            ugm.users['max']['foo'] = user
        err = self.expect_error(NotImplementedError, __setitem__fails)
        expected = 'User does not implement ``__setitem__``'
        self.assertEqual(str(err), expected)

    def test_group(self):
        ugm = self._create_ugm()
        ugm()

        # Add users
        ugm.users.create('max', fullname='Max', email='foo@bar.com')
        ugm.users.create('sepp', fullname='Sepp', email='baz@bar.com')

        # Add new Group
        group = ugm.groups.create('group1', description='Group 1')
        expected = '<Group object \'group1\' at '
        self.assertTrue(str(group).startswith(expected))
        self.assertEqual(ugm.treerepr(), (
            '<class \'node.ext.ugm.file.Ugm\'>: ugm\n'
            '  <class \'node.ext.ugm.file.Users\'>: users\n'
            '    <class \'node.ext.ugm.file.User\'>: max\n'
            '    <class \'node.ext.ugm.file.User\'>: sepp\n'
            '  <class \'node.ext.ugm.file.Groups\'>: groups\n'
            '    <class \'node.ext.ugm.file.Group\'>: group1\n'
        ))

        # Nothing written yet
        with open(ugm.groups.file_path) as f:
            lines = f.readlines()
        self.assertEqual(lines, [])

        self.check_output("""\
        /.../principal_data/groups/group1
        """, group.attrs.file_path)

        err = self.expect_error(IOError, open, group.attrs.file_path)
        self.check_output("""\
        [Errno 2] No such file or directory: '/.../groups/group1'
        """, str(err))

        # Persist and read related files again
        ugm()
        with open(ugm.groups.file_path) as f:
            lines = f.readlines()
        self.assertEqual(lines, ['group1:\n'])

        with open(group.attrs.file_path) as f:
            lines = f.readlines()
        self.assertEqual(lines, ['description:Group 1\n'])

        # No members yet
        self.assertEqual(group.member_ids, [])

        # Setitem is forbidden on a group
        def __setitem__fails():
            group['foo'] = ugm.users['max']
        err = self.expect_error(NotImplementedError, __setitem__fails)
        expected = 'Group does not implement ``__setitem__``'
        self.assertEqual(str(err), expected)

        # A user is added to a group via ``add``
        id = ugm.users['max'].name
        self.assertEqual(id, 'max')

        group.add(id)
        self.assertEqual(group.member_ids, ['max'])
        self.assertEqual(group.users, [ugm.users['max']])
        self.assertEqual(group['max'], ugm.users['max'])

        # Nothing written yet
        with open(ugm.groups.file_path) as f:
            lines = f.readlines()
        self.assertEqual(lines, ['group1:\n'])

        ugm()
        with open(ugm.groups.file_path) as f:
            lines = f.readlines()
        self.assertEqual(lines, ['group1:max\n'])

        # Note, parent of returned user is users object, not group
        self.assertEqual(group['max'].path, ['ugm', 'users', 'max'])

        # Add another Group and add members
        group = ugm.groups.create('group2', description='Group 2')
        expected = '<Group object \'group2\' at '
        self.assertTrue(str(group).startswith(expected))
        group.add('max')
        group.add('sepp')
        self.assertEqual(ugm.treerepr(), (
            '<class \'node.ext.ugm.file.Ugm\'>: ugm\n'
            '  <class \'node.ext.ugm.file.Users\'>: users\n'
            '    <class \'node.ext.ugm.file.User\'>: max\n'
            '    <class \'node.ext.ugm.file.User\'>: sepp\n'
            '  <class \'node.ext.ugm.file.Groups\'>: groups\n'
            '    <class \'node.ext.ugm.file.Group\'>: group1\n'
            '      <class \'node.ext.ugm.file.User\'>: max\n'
            '    <class \'node.ext.ugm.file.Group\'>: group2\n'
            '      <class \'node.ext.ugm.file.User\'>: max\n'
            '      <class \'node.ext.ugm.file.User\'>: sepp\n'
        ))

        with open(ugm.groups.file_path) as f:
            lines = f.readlines()
        self.assertEqual(lines, ['group1:max\n'])

        ugm()
        with open(ugm.groups.file_path) as f:
            lines = f.readlines()
        self.assertEqual(lines, [
            'group1:max\n',
            'group2:max,sepp\n'
        ])

    def test_groups_on_user(self):
        ugm = self._create_ugm()
        ugm.users.create('max', fullname='Max', email='foo@bar.com')
        ugm.users.create('sepp', fullname='Sepp', email='baz@bar.com')
        group1 = ugm.groups.create('group1', description='Group 1')
        group1.add('max')
        group2 = ugm.groups.create('group2', description='Group 2')
        group2.add('max')
        group2.add('sepp')
        ugm()

        # ``groups`` attribute on user
        max = ugm.users['max']
        self.assertEqual(max.groups, [group1, group2])
        sepp = ugm.users['sepp']
        self.assertEqual(sepp.groups, [group2])

        # ``group_ids`` attribute on user
        self.assertEqual(max.group_ids, ['group1', 'group2'])
        self.assertEqual(sepp.group_ids, ['group2'])

    def test__compare_value(self):
        ugm = self._create_ugm()
        _compare_value = ugm.users._compare_value
        self.assertTrue(_compare_value('*', ''))
        self.assertFalse(_compare_value('**', ''))
        self.assertTrue(_compare_value('aa', 'aa'))
        self.assertFalse(_compare_value('aa', 'aaa'))
        self.assertTrue(_compare_value('*a*', 'abc'))
        self.assertFalse(_compare_value('*a', 'abc'))
        self.assertTrue(_compare_value('*c', 'abc'))
        self.assertTrue(_compare_value('a*', 'abc'))
        self.assertFalse(_compare_value('c*', 'abc'))

    def test_search_users(self):
        ugm = self._create_ugm()
        ugm.users.create('max', fullname='Max Muster', email='foo@bar.com')
        ugm.users.create('sepp', fullname='Sepp Muster', email='baz@bar.com')
        ugm.users.create('maxii')
        ugm.users.create('123sepp')
        ugm()

        users = ugm.users
        self.assertEqual(
            sorted(users.keys()),
            ['123sepp', 'max', 'maxii', 'sepp']
        )

        # Test Search on users
        self.assertEqual(users.search(), [])
        self.assertEqual(users.search(criteria=dict(id='max')), ['max'])
        self.assertEqual(
            sorted(users.search(criteria=dict(id='max*'))),
            ['max', 'maxii']
        )
        self.assertEqual(users.search(criteria=dict(id='sepp')), ['sepp'])
        self.assertEqual(
            sorted(users.search(criteria=dict(id='*sep*'))),
            ['123sepp', 'sepp']
        )

        # Search on users exact match
        self.assertEqual(
            users.search(criteria=dict(id='max'), exact_match=True),
            ['max']
        )
        def search_fails():
            users.search(criteria=dict(id='max*'), exact_match=True)
        err = self.expect_error(ValueError, search_fails)
        expected = 'Exact match asked but result not unique'
        self.assertEqual(str(err), expected)

        def search_fails2():
            users.search(criteria=dict(id='inexistent'), exact_match=True)
        err = self.expect_error(ValueError, search_fails2)
        expected = 'Exact match asked but result length is zero'
        self.assertEqual(str(err), expected)

        # Search on users attribute list
        res = users.search(
            criteria=dict(id='max'),
            attrlist=['fullname', 'email']
        )
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][0], 'max')
        self.assertEqual(res[0][1], {
            'email': 'foo@bar.com',
            'fullname': 'Max Muster'
        })

        res = sorted(users.search(
            criteria=dict(id='max*'),
            attrlist=['fullname', 'email']
        ))
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0][0], 'max')
        self.assertEqual(res[0][1], {
            'email': 'foo@bar.com',
            'fullname': 'Max Muster'
        })
        self.assertEqual(res[1][0], 'maxii')
        self.assertEqual(res[1][1], {
            'email': '',
            'fullname': ''
        })

        res = sorted(users.search(
            criteria=dict(id='*ax*'),
            attrlist=['id']
        ))
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0][0], 'max')
        self.assertEqual(res[0][1], {'id': 'max'})
        self.assertEqual(res[1][0], 'maxii')
        self.assertEqual(res[1][1], {'id': 'maxii'})

        # Search on users or search
        res = sorted(users.search(
            criteria=dict(fullname='*Muster*', id='max*'),
            or_search=True
        ))
        self.assertEqual(res, ['max', 'maxii', 'sepp'])

        res = users.search(
            criteria=dict(fullname='*Muster*', id='max*'),
            or_search=False
        )
        self.assertEqual(res, ['max'])

    def test_search_groups(self):
        ugm = self._create_ugm()
        ugm.groups.create('group1', description='Group 1 Description')
        ugm.groups.create('group2', description='Group 2 Description')
        ugm.groups.create('group3')
        ugm()

        groups = ugm.groups
        self.assertEqual(sorted(groups.keys()), ['group1', 'group2', 'group3'])

        # Test Search on groups
        self.assertEqual(groups.search(criteria=dict(id='group1')), ['group1'])
        self.assertEqual(
            sorted(groups.search(criteria=dict(id='group*'))),
            ['group1', 'group2', 'group3']
        )
        self.assertEqual(
            sorted(groups.search(criteria=dict(id='*rou*'))),
            ['group1', 'group2', 'group3']
        )
        self.assertEqual(groups.search(criteria=dict(id='*3')), ['group3'])

        # Search on groups exact match
        self.assertEqual(
            groups.search(criteria=dict(id='group1'), exact_match=True),
            ['group1']
        )

        def search_fails():
            groups.search(criteria=dict(id='group*'), exact_match=True)
        err = self.expect_error(ValueError, search_fails)
        expected = 'Exact match asked but result not unique'
        self.assertEqual(str(err), expected)

        def search_fails2():
            groups.search(criteria=dict(id='inexistent'), exact_match=True)
        err = self.expect_error(ValueError, search_fails2)
        expected = 'Exact match asked but result length is zero'
        self.assertEqual(str(err), expected)

        # Search on groups attribute list
        res = sorted(groups.search(
            criteria=dict(id='group*'),
            attrlist=['description']
        ))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0][0], 'group1')
        self.assertEqual(res[0][1], {'description': 'Group 1 Description'})
        self.assertEqual(res[1][0], 'group2')
        self.assertEqual(res[1][1], {'description': 'Group 2 Description'})
        self.assertEqual(res[2][0], 'group3')
        self.assertEqual(res[2][1], {'description': ''})

        res = groups.search(
            criteria=dict(id='*2'),
            attrlist=['id', 'description']
        )
        self.assertEqual(res, [
            ('group2', {'id': 'group2', 'description': 'Group 2 Description'})
        ])

        # Search on groups or search
        res = sorted(groups.search(
            criteria=dict(description='*Desc*', id='*g*'),
            or_search=True
        ))
        self.assertEqual(res, ['group1', 'group2', 'group3'])

        res = groups.search(
            criteria=dict(description='*Desc*', id='*1'),
            or_search=False
        )
        self.assertEqual(res, ['group1'])

        res = groups.search(
            criteria=dict(description='*Desc*', id='*3'),
            or_search=False
        )
        self.assertEqual(res, [])

    def test_delete_user_from_group(self):
        ugm = self._create_ugm()
        ugm.users.create('max', fullname='Max Muster', email='foo@bar.com')
        ugm.users.create('sepp', fullname='Sepp Muster', email='baz@bar.com')
        ugm.groups.create('group1', description='Group 1 Description')
        ugm.groups.create('group2', description='Group 2 Description')
        ugm.groups['group1'].add('max')
        ugm.groups['group2'].add('max')
        ugm.groups['group2'].add('sepp')
        ugm()
        self.assertEqual(ugm.treerepr(), (
            '<class \'node.ext.ugm.file.Ugm\'>: ugm\n'
            '  <class \'node.ext.ugm.file.Users\'>: users\n'
            '    <class \'node.ext.ugm.file.User\'>: max\n'
            '    <class \'node.ext.ugm.file.User\'>: sepp\n'
            '  <class \'node.ext.ugm.file.Groups\'>: groups\n'
            '    <class \'node.ext.ugm.file.Group\'>: group1\n'
            '      <class \'node.ext.ugm.file.User\'>: max\n'
            '    <class \'node.ext.ugm.file.Group\'>: group2\n'
            '      <class \'node.ext.ugm.file.User\'>: max\n'
            '      <class \'node.ext.ugm.file.User\'>: sepp\n'
        ))

        # Delete user from group
        def __delitem__fails():
            del ugm.groups['group2']['inexistent']
        err = self.expect_error(KeyError, __delitem__fails)
        expected = '\'inexistent\''
        self.assertEqual(str(err), expected)

        del ugm.groups['group2']['max']
        self.assertEqual(ugm.groups.treerepr(), (
            '<class \'node.ext.ugm.file.Groups\'>: groups\n'
            '  <class \'node.ext.ugm.file.Group\'>: group1\n'
            '    <class \'node.ext.ugm.file.User\'>: max\n'
            '  <class \'node.ext.ugm.file.Group\'>: group2\n'
            '    <class \'node.ext.ugm.file.User\'>: sepp\n'
        ))

        # Not persisted yet
        with open(ugm.groups.file_path) as f:
            lines = f.readlines()
        self.assertEqual(sorted(lines), [
            'group1:max\n',
            'group2:max,sepp\n'
        ])

        # Call tree and check result
        ugm()
        with open(ugm.groups.file_path) as f:
            lines = f.readlines()
        self.assertEqual(sorted(lines), [
            'group1:max\n',
            'group2:sepp\n'
        ])

    def test_user_roles(self):
        pass

"""
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

    >>> with open(ugm.roles_file) as file:
    ...     print file.readlines()
    []

After ``__call__`` roles are persisted::

    >>> user()
    >>> with open(ugm.roles_file) as file:
    ...     file.readlines()
    ['max::manager\n']

Add role for User via Ugm object::

    >>> ugm.add_role('supervisor', user)
    >>> user.roles
    ['manager', 'supervisor']

    >>> ugm.roles(user) == user.roles
    True

Call and check result::

    >>> ugm()
    >>> with open(ugm.roles_file) as file:
    ...     print file.readlines()
    ['max::manager,supervisor\n']

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
    >>> with open(ugm.roles_file) as file:
    ...     print file.readlines()
    ['max::manager\n']

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

    >>> with open(ugm.roles_file) as file:
    ...     print file.readlines()
    ['max::manager\n']

After ``__call__`` roles are persisted::

    >>> group()
    >>> with open(ugm.roles_file) as file:
    ...     print file.readlines()
    ['max::manager\n',
    'group:group1::authenticated\n']

Add role for Group via Ugm object::

    >>> ugm.add_role('editor', group)
    >>> group.roles
    ['authenticated', 'editor']

    >>> ugm.roles(group) == group.roles
    True

Call and check result::

    >>> ugm()
    >>> with open(ugm.roles_file) as file:
    ...     print file.readlines()
    ['max::manager\n',
    'group:group1::authenticated,editor\n']

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
    >>> with open(ugm.roles_file) as file:
    ...     print file.readlines()
    ['max::manager\n',
    'group:group1::authenticated\n']

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
    >>> with open(ugm.users.file_path) as file:
    ...     print file.readlines()
    ['sepp:...\n']

User data is deleted::

    >>> os.listdir(os.path.join(ugm.data_directory, 'users'))
    ['sepp']

Roles for user are deleted as well::

    >>> with open(ugm.roles_file) as file:
    ...     print file.readlines()
    ['group:group1::authenticated\n']

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
    >>> with open(ugm.groups.file_path) as file:
    ...     print file.readlines()
    ['group2:sepp\n']

Group data is deleted::

    >>> os.listdir(os.path.join(ugm.data_directory, 'groups'))
    ['group2']

Roles for group are deleted as well::

    >>> with open(ugm.roles_file) as file:
    ...     print file.readlines()
    []

"""