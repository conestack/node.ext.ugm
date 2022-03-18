from __future__ import print_function
from node.behaviors import Attributes
from node.behaviors import DefaultInit
from node.behaviors import MappingAdopt
from node.behaviors import MappingConstraints
from node.behaviors import MappingNode
from node.ext.ugm.file import FileStorage
from node.ext.ugm.file import Ugm
from node.tests import NodeTestCase
from node.utils import UNSET
from plumber import plumbing
import os
import shutil
import tempfile


###############################################################################
# Mock objects
###############################################################################

@plumbing(
    MappingConstraints,
    MappingAdopt,
    Attributes,
    DefaultInit,
    MappingNode,
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

    def _read_file(self, file_path):
        with open(file_path) as f:
            lines = f.readlines()
        return lines

    def _create_ugm(self):
        # Create principal data directory
        datadir = os.path.join(self.tempdir, 'principal_data')
        if not os.path.exists(datadir):
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
        fsn['foo'] = u'foo'
        fsn['bar'] = u'bar'
        fsn['baz'] = u'baz'
        fsn['none'] = None
        fsn['unset'] = UNSET

        # __getitem__
        with self.assertRaises(KeyError) as arc:
            fsn['inexistent']
        self.assertEqual(str(arc.exception), '\'inexistent\'')
        self.assertEqual(fsn['foo'], 'foo')
        self.assertEqual(fsn['none'], None)
        self.assertEqual(fsn['unset'], UNSET)

        # __iter__
        self.assertEqual(
            list(fsn.keys()),
            ['foo', 'bar', 'baz', 'none', 'unset']
        )

        # __delitem__
        with self.assertRaises(KeyError) as arc:
            del fsn['inexistent']
        self.assertEqual(str(arc.exception), '\'inexistent\'')
        del fsn['baz']

        # File not written yet
        with self.assertRaises(IOError) as arc:
            open(file_path)
        self.checkOutput("""\
        [Errno 2] No such file or directory: '/.../filestorage'
        """, str(arc.exception))

        # Persist and check written file
        fsn()
        lines = self._read_file(file_path)
        self.assertEqual(lines, [
            'foo:foo\n',
            'bar:bar\n',
            'none:\n',
            'unset:\n'
        ])

        # Recreate
        fsn = FileStorageNode(file_path)
        self.assertEqual(list(fsn.keys()), [u'foo', u'bar', u'none', u'unset'])
        self.assertEqual(list(fsn.values()), [u'foo', u'bar', u'', u''])

        # Test unicode
        fsn[u'\xe4\xf6\xfc'] = u'\xe4\xf6\xfc'
        fsn()
        fsn = FileStorageNode(file_path)
        self.assertEqual(sorted(list(fsn.items())), [
            (u'bar', u'bar'),
            (u'foo', u'foo'),
            (u'none', u''),
            (u'unset', u''),
            (u'\xe4\xf6\xfc', u'\xe4\xf6\xfc')
        ])

        # Test binary data
        fsn[u'binary'] = b'Hello'
        fsn()
        fsn = FileStorageNode(file_path)
        self.assertEqual(sorted(list(fsn.items())), [
            (u'bar', u'bar'),
            (u'binary', b'Hello'),
            (u'foo', u'foo'),
            (u'none', u''),
            (u'unset', u''),
            (u'\xe4\xf6\xfc', u'\xe4\xf6\xfc')
        ])
        lines = self._read_file(file_path)
        self.assertTrue('binary:b64:SGVsbG8=\n' in lines)

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

        with self.assertRaises(KeyError) as arc:
            ugm['inexistent'] = ugm.users
        self.assertEqual(str(arc.exception), '\'inexistent\'')

        with self.assertRaises(NotImplementedError) as arc:
            del ugm['users']
        self.assertEqual(
            str(arc.exception),
            'Operation forbidden on this node.'
        )

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

        # Invalidate
        self.assertEqual(ugm.storage.keys(), ['users', 'groups'])
        ugm.invalidate(key='users')
        self.assertEqual(ugm.storage.keys(), ['groups'])
        ugm.invalidate()
        self.assertEqual(ugm.storage.keys(), [])

    def test_user(self):
        ugm = self._create_ugm()
        ugm()

        # Add new User
        user = ugm.users.create('max', fullname=u'Max', email=u'foo@bar.com')
        expected = '<User object \'max\' at '
        self.assertTrue(str(user).startswith(expected))
        self.assertEqual(ugm.treerepr(), (
            '<class \'node.ext.ugm.file.Ugm\'>: ugm\n'
            '  <class \'node.ext.ugm.file.Users\'>: users\n'
            '    <class \'node.ext.ugm.file.User\'>: max\n'
            '  <class \'node.ext.ugm.file.Groups\'>: groups\n'
        ))

        # Nothing written yet
        lines = self._read_file(ugm.users.file_path)
        self.assertEqual(lines, [])

        self.checkOutput("""\
        /.../principal_data/users/max
        """, user.attrs.file_path)

        with self.assertRaises(IOError) as arc:
            open(user.attrs.file_path)
        self.checkOutput("""\
        [Errno 2] No such file or directory: '/.../users/max'
        """, str(arc.exception))

        # Persist and read related files again
        ugm()
        lines = self._read_file(ugm.users.file_path)
        self.assertEqual(lines, ['max:\n'])

        lines = self._read_file(user.attrs.file_path)
        self.assertEqual(sorted(lines), [
            'email:foo@bar.com\n',
            'fullname:Max\n'
        ])

        # Authentication is prohibited for users without a password
        self.assertFalse(ugm.users.authenticate('max', 'secret'))

        # Set Password for new User
        ugm.users.passwd('max', None, 'secret')
        ugm()
        lines = self._read_file(ugm.users.file_path)
        self.checkOutput("""\
        ['max:...\\n']
        """, str(lines))

        # Password for inextistent user
        with self.assertRaises(ValueError) as arc:
            ugm.users.passwd('sepp', None, 'secret')
        self.assertEqual(
            str(arc.exception),
            'User with id \'sepp\' does not exist.'
        )

        # Password with wrong oldpw
        with self.assertRaises(ValueError) as arc:
            ugm.users.passwd('max', 'wrong', 'new')
        self.assertEqual(
            str(arc.exception),
            'Old password does not match.'
        )

        # Set new password for max
        ugm.users.passwd('max', 'secret', 'secret1')
        ugm()
        lines = self._read_file(ugm.users.file_path)
        self.checkOutput("""\
        ['max:...\\n']
        """, str(lines))

        # Authentication
        self.assertFalse(ugm.users.authenticate('inexistent', 'secret'))
        self.assertFalse(ugm.users.authenticate('max', 'secret'))
        self.assertTrue(ugm.users.authenticate('max', 'secret1'))

        # Add another user
        user = ugm.users.create('sepp', fullname=u'Sepp', email=u'baz@bar.com')
        ugm.users.passwd('sepp', None, 'secret')
        ugm()
        self.assertEqual(ugm.treerepr(), (
            '<class \'node.ext.ugm.file.Ugm\'>: ugm\n'
            '  <class \'node.ext.ugm.file.Users\'>: users\n'
            '    <class \'node.ext.ugm.file.User\'>: max\n'
            '    <class \'node.ext.ugm.file.User\'>: sepp\n'
            '  <class \'node.ext.ugm.file.Groups\'>: groups\n'
        ))
        lines = self._read_file(ugm.users.file_path)
        self.checkOutput("""\
        ['max:...\\n',
        'sepp:...\\n']
        """, str(lines))

        # ``__setitem__`` on user is prohibited
        with self.assertRaises(NotImplementedError) as arc:
            ugm.users['max']['foo'] = user
        self.assertEqual(
            str(arc.exception),
            'User does not support ``__setitem__``'
        )

    def test_group(self):
        ugm = self._create_ugm()
        ugm()

        # Add users
        ugm.users.create('max', fullname=u'Max', email=u'foo@bar.com')
        ugm.users.create('sepp', fullname=u'Sepp', email=u'baz@bar.com')

        # Add new Group
        group = ugm.groups.create('group1', description=u'Group 1')
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
        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(lines, [])

        self.checkOutput("""\
        /.../principal_data/groups/group1
        """, group.attrs.file_path)

        with self.assertRaises(IOError) as arc:
            open(group.attrs.file_path)
        self.checkOutput("""\
        [Errno 2] No such file or directory: '/.../groups/group1'
        """, str(arc.exception))

        # Persist and read related files again
        ugm()
        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(lines, ['group1:\n'])

        lines = self._read_file(group.attrs.file_path)
        self.assertEqual(lines, ['description:Group 1\n'])

        # No members yet
        self.assertEqual(group.member_ids, [])

        # Setitem is forbidden on a group
        with self.assertRaises(NotImplementedError) as arc:
            group['foo'] = ugm.users['max']
        self.assertEqual(
            str(arc.exception),
            'Group does not support ``__setitem__``'
        )

        # A user is added to a group via ``add``
        id = ugm.users['max'].name
        self.assertEqual(id, 'max')

        group.add(id)
        self.assertEqual(group.member_ids, ['max'])
        self.assertEqual(group.users, [ugm.users['max']])
        self.assertEqual(group['max'], ugm.users['max'])

        # Nothing written yet
        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(lines, ['group1:\n'])

        ugm()
        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(lines, ['group1:max\n'])

        # Note, parent of returned user is users object, not group
        self.assertEqual(group['max'].path, ['ugm', 'users', 'max'])

        # Add another Group and add members
        group = ugm.groups.create('group2', description=u'Group 2')
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

        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(lines, ['group1:max\n'])

        ugm()
        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(lines, [
            'group1:max\n',
            'group2:max,sepp\n'
        ])

    def test_groups_on_user(self):
        ugm = self._create_ugm()
        ugm.users.create('max', fullname=u'Max', email=u'foo@bar.com')
        ugm.users.create('sepp', fullname=u'Sepp', email=u'baz@bar.com')
        group1 = ugm.groups.create('group1', description=u'Group 1')
        group1.add('max')
        group2 = ugm.groups.create('group2', description=u'Group 2')
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
        ugm.users.create('max', fullname=u'Max Muster', email=u'foo@bar.com')
        ugm.users.create('sepp', fullname=u'Sepp Muster', email=u'baz@bar.com')
        ugm.users.create('maxii')
        ugm.users.create('123sepp')
        ugm()

        users = ugm.users
        self.assertEqual(
            sorted(users.keys()),
            ['123sepp', 'max', 'maxii', 'sepp']
        )

        # Test Search on users
        self.assertEqual(
            sorted(users.search()),
            ['123sepp', 'max', 'maxii', 'sepp']
        )
        self.assertEqual(
            sorted(users.search(criteria=dict())),
            ['123sepp', 'max', 'maxii', 'sepp']
        )
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

        with self.assertRaises(ValueError) as arc:
            users.search(criteria=dict(id='max*'), exact_match=True)
        self.assertEqual(
            str(arc.exception),
            'Exact match asked but result not unique'
        )

        with self.assertRaises(ValueError) as arc:
            users.search(criteria=dict(id='inexistent'), exact_match=True)
        self.assertEqual(
            str(arc.exception),
            'Exact match asked but result length is zero'
        )

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
        ugm.groups.create('group1', description=u'Group 1 Description')
        ugm.groups.create('group2', description=u'Group 2 Description')
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

        with self.assertRaises(ValueError) as arc:
            groups.search(criteria=dict(id='group*'), exact_match=True)
        self.assertEqual(
            str(arc.exception),
            'Exact match asked but result not unique'
        )

        with self.assertRaises(ValueError) as arc:
            groups.search(criteria=dict(id='inexistent'), exact_match=True)
        self.assertEqual(
            str(arc.exception),
            'Exact match asked but result length is zero'
        )

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
        ugm.users.create('max', fullname=u'Max Muster', email=u'foo@bar.com')
        ugm.users.create('sepp', fullname=u'Sepp Muster', email=u'baz@bar.com')
        ugm.groups.create('group1', description=u'Group 1 Description')
        ugm.groups.create('group2', description=u'Group 2 Description')
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
        with self.assertRaises(KeyError) as arc:
            del ugm.groups['group2']['inexistent']
        self.assertEqual(str(arc.exception), '\'inexistent\'')

        del ugm.groups['group2']['max']
        self.assertEqual(ugm.groups.treerepr(), (
            '<class \'node.ext.ugm.file.Groups\'>: groups\n'
            '  <class \'node.ext.ugm.file.Group\'>: group1\n'
            '    <class \'node.ext.ugm.file.User\'>: max\n'
            '  <class \'node.ext.ugm.file.Group\'>: group2\n'
            '    <class \'node.ext.ugm.file.User\'>: sepp\n'
        ))

        # Not persisted yet
        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(sorted(lines), [
            'group1:max\n',
            'group2:max,sepp\n'
        ])

        # Call tree and check result
        ugm()
        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(sorted(lines), [
            'group1:max\n',
            'group2:sepp\n'
        ])

    def test_user_roles(self):
        ugm = self._create_ugm()
        ugm.users.create('max', fullname=u'Max Muster', email=u'foo@bar.com')
        ugm()

        # No roles yet
        user = ugm.users['max']
        self.assertEqual(user.roles, [])

        # Add role via User object
        user.add_role('manager')
        self.assertEqual(user.roles, ['manager'])

        # Add same role twice fails
        with self.assertRaises(ValueError) as arc:
            user.add_role('manager')
        self.assertEqual(
            str(arc.exception),
            'Principal already has role \'manager\''
        )

        # Not written yet
        lines = self._read_file(ugm.roles_file)
        self.assertEqual(lines, [])

        # After ``__call__`` roles are persisted
        user()
        lines = self._read_file(ugm.roles_file)
        self.assertEqual(lines, ['max::manager\n'])

        # Add role for User via Ugm object
        ugm.add_role('supervisor', user)
        self.assertEqual(user.roles, ['manager', 'supervisor'])
        self.assertTrue(ugm.roles(user) == user.roles)

        # Call and check result
        ugm()
        lines = self._read_file(ugm.roles_file)
        self.assertEqual(lines, ['max::manager,supervisor\n'])

        # Remove User role
        user.remove_role('supervisor')
        self.assertEqual(user.roles, ['manager'])

        # Remove inexistent role fails
        with self.assertRaises(ValueError) as arc:
            user.remove_role('supervisor')
        self.assertEqual(
            str(arc.exception),
            'Principal does not has role \'supervisor\''
        )

        # Call persists
        user()
        lines = self._read_file(ugm.roles_file)
        self.assertEqual(lines, ['max::manager\n'])

    def test_group_roles(self):
        ugm = self._create_ugm()
        ugm.users.create('max')
        ugm.groups.create('group1', description=u'Group 1 Description')
        ugm.groups['group1'].add('max')
        ugm()

        # No roles yet
        group = ugm.groups['group1']
        self.assertEqual(group.roles, [])

        # Add role via Group object
        group.add_role('authenticated')
        self.assertEqual(group.roles, ['authenticated'])

        # Add same role twice fails
        with self.assertRaises(ValueError) as arc:
            group.add_role('authenticated')
        self.assertEqual(
            str(arc.exception),
            'Principal already has role \'authenticated\''
        )

        # Group role not written yet
        lines = self._read_file(ugm.roles_file)
        self.assertEqual(lines, [])

        # After ``__call__`` roles are persisted
        group()
        lines = self._read_file(ugm.roles_file)
        self.assertEqual(lines, ['group:group1::authenticated\n'])

        # Add role for Group via Ugm object
        ugm.add_role('editor', group)
        self.assertEqual(group.roles, ['authenticated', 'editor'])
        self.assertTrue(ugm.roles(group) == group.roles)

        # Call and check result
        ugm()
        lines = self._read_file(ugm.roles_file)
        self.assertEqual(lines, ['group:group1::authenticated,editor\n'])

        # Remove Group role
        group.remove_role('editor')
        self.assertEqual(group.roles, ['authenticated'])

        # Remove inexistent role fails
        with self.assertRaises(ValueError) as arc:
            group.remove_role('editor')
        self.assertEqual(
            str(arc.exception),
            'Principal does not has role \'editor\''
        )

        # Call persists
        group()
        lines = self._read_file(ugm.roles_file)
        self.assertEqual(lines, ['group:group1::authenticated\n'])

    def test_users(self):
        ugm = self._create_ugm()
        ugm.users.create('max', fullname=u'Max Muster', email=u'foo@bar.com')
        ugm.users['max'].add_role('manager')
        ugm.groups.create('group1', description=u'Group 1 Description')
        ugm.groups.create('group2', description=u'Group 2 Description')
        ugm.groups['group1'].add('max')
        ugm.groups['group2'].add('max')
        ugm()

        lines = self._read_file(ugm.users.file_path)
        self.assertEqual(sorted(lines), ['max:\n'])

        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(sorted(lines), ['group1:max\n', 'group2:max\n'])

        lines = self._read_file(ugm.roles_file)
        self.assertEqual(sorted(lines), ['max::manager\n'])

        self.assertEqual(
            os.listdir(os.path.join(ugm.data_directory, 'users')),
            ['max']
        )

        # Recreate ugm object
        ugm = self._create_ugm()

        # XXX: id_for_login actually just returns given login name
        self.assertEqual(ugm.users.id_for_login('max'), 'max')

        with self.assertRaises(KeyError) as arc:
            ugm.users['inexistent']
        self.assertEqual(str(arc.exception), '\'inexistent\'')

        expected = '<User object \'max\' at '
        self.assertTrue(str(ugm.users['max']).startswith(expected))

        # Delete user. User gets removed from groups and roles
        del ugm.users['max']
        self.assertEqual(ugm.treerepr(), (
            '<class \'node.ext.ugm.file.Ugm\'>: ugm\n'
            '  <class \'node.ext.ugm.file.Users\'>: users\n'
            '  <class \'node.ext.ugm.file.Groups\'>: groups\n'
            '    <class \'node.ext.ugm.file.Group\'>: group1\n'
            '    <class \'node.ext.ugm.file.Group\'>: group2\n'
        ))
        ugm.users()

        lines = self._read_file(ugm.users.file_path)
        self.assertEqual(sorted(lines), [])

        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(sorted(lines), ['group1:\n', 'group2:\n'])

        lines = self._read_file(ugm.roles_file)
        self.assertEqual(sorted(lines), [])

        # User data is deleted as well
        self.assertEqual(
            os.listdir(os.path.join(ugm.data_directory, 'users')),
            []
        )

    def test_groups(self):
        ugm = self._create_ugm()
        ugm.users.create('max', fullname=u'Max Muster', email=u'foo@bar.com')
        ugm.groups.create('group1', description=u'Group 1 Description')
        ugm.groups['group1'].add('max')
        ugm.groups['group1'].add_role('manager')

        self.assertEqual(ugm.users['max'].groups, [ugm.groups['group1']])
        self.assertEqual(ugm.groups['group1'].roles, ['manager'])

        ugm()

        lines = self._read_file(ugm.users.file_path)
        self.assertEqual(sorted(lines), ['max:\n'])

        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(sorted(lines), ['group1:max\n'])

        lines = self._read_file(ugm.roles_file)
        self.assertEqual(sorted(lines), ['group:group1::manager\n'])

        self.assertEqual(
            os.listdir(os.path.join(ugm.data_directory, 'groups')),
            ['group1']
        )

        # Recreate ugm object
        ugm = self._create_ugm()

        with self.assertRaises(KeyError) as arc:
            ugm.groups['inexistent']
        self.assertEqual(str(arc.exception), '\'inexistent\'')

        with self.assertRaises(KeyError) as arc:
            ugm.groups['group1'].add('inexistent')
        self.assertEqual(str(arc.exception), '\'inexistent\'')

        expected = '<Group object \'group1\' at '
        self.assertTrue(str(ugm.groups['group1']).startswith(expected))

        # Delete group. Group gets removed from user and from roles
        del ugm.groups['group1']
        self.assertEqual(ugm.treerepr(), (
            '<class \'node.ext.ugm.file.Ugm\'>: ugm\n'
            '  <class \'node.ext.ugm.file.Users\'>: users\n'
            '    <class \'node.ext.ugm.file.User\'>: max\n'
            '  <class \'node.ext.ugm.file.Groups\'>: groups\n'
        ))
        self.assertEqual(ugm.users['max'].groups, [])
        ugm.groups()

        lines = self._read_file(ugm.users.file_path)
        self.assertEqual(sorted(lines), ['max:\n'])

        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(sorted(lines), [])

        lines = self._read_file(ugm.roles_file)
        self.assertEqual(sorted(lines), [])

        # Group data is deleted as well
        self.assertEqual(
            os.listdir(os.path.join(ugm.data_directory, 'groups')),
            []
        )
