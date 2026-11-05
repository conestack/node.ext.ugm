from datetime import datetime
from datetime import timedelta
from node.behaviors import Attributes
from node.behaviors import MappingAdopt
from node.behaviors import MappingConstraints
from node.behaviors import MappingNode
from node.ext.ugm import file as file_module
from node.ext.ugm.file import FileStorage
from node.ext.ugm.file import Ugm
from node.ext.ugm.password import check_password
from node.ext.ugm.password import hash_password
from node.ext.ugm.password import wrap_legacy_hash
from node.ext.ugm.wrap_passwords import main as wrap_passwords
from node.tests import NodeTestCase
from node.utils import UNSET
from plumber import plumbing
from unittest import mock
import base64
import hashlib
import os
import shutil
import stat
import tempfile


###############################################################################
# Mock objects
###############################################################################


@plumbing(MappingConstraints, MappingAdopt, Attributes, MappingNode, FileStorage)
class FileStorageNode:
    """File storage."""

    def __init__(self, file_path):
        self.__name__ = None
        self.__parent__ = None
        self.file_path = file_path
        self._storage_data = None


###############################################################################
# Tests
###############################################################################


def legacy_hash(value, salt=b'12345678'):
    digest = hashlib.sha256(value.encode('utf-8') + salt).digest()
    return base64.b64encode(digest + salt).decode()


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
            data_directory=datadir,
        )

    def test_file_storage(self):
        file_path = os.path.join(self.tempdir, 'filestorage')
        fsn = FileStorageNode(file_path)

        expected = "<FileStorageNode object 'None' at "
        self.assertTrue(str(fsn).startswith(expected))
        self.assertEqual(list(fsn.__iter__()), [])

        # __setitem__
        fsn['foo'] = 'foo'
        fsn['bar'] = 'bar'
        fsn['baz'] = 'baz'
        fsn['none'] = None
        fsn['unset'] = UNSET

        # __getitem__
        with self.assertRaises(KeyError) as arc:
            fsn['inexistent']
        self.assertEqual(str(arc.exception), "'inexistent'")
        self.assertEqual(fsn['foo'], 'foo')
        self.assertEqual(fsn['none'], None)
        self.assertEqual(fsn['unset'], UNSET)

        # __iter__
        self.assertEqual(list(fsn.keys()), ['foo', 'bar', 'baz', 'none', 'unset'])

        # __delitem__
        with self.assertRaises(KeyError) as arc:
            del fsn['inexistent']
        self.assertEqual(str(arc.exception), "'inexistent'")
        del fsn['baz']

        # File not written yet
        with self.assertRaises(IOError) as arc:
            open(file_path)
        self.checkOutput(
            """\
        [Errno 2] No such file or directory: '/.../filestorage'
        """,
            str(arc.exception),
        )

        # Persist and check written file
        fsn()
        lines = self._read_file(file_path)
        self.assertEqual(lines, ['foo:foo\n', 'bar:bar\n', 'none:\n', 'unset:\n'])

        # Recreate
        fsn = FileStorageNode(file_path)
        self.assertEqual(list(fsn.keys()), ['foo', 'bar', 'none', 'unset'])
        self.assertEqual(list(fsn.values()), ['foo', 'bar', '', ''])

        # Test unicode
        fsn['\xe4\xf6\xfc'] = '\xe4\xf6\xfc'
        fsn()
        fsn = FileStorageNode(file_path)
        self.assertEqual(
            sorted(list(fsn.items())),
            [
                ('bar', 'bar'),
                ('foo', 'foo'),
                ('none', ''),
                ('unset', ''),
                ('\xe4\xf6\xfc', '\xe4\xf6\xfc'),
            ],
        )

        # Test binary data
        fsn['binary'] = b'Hello'
        fsn()
        fsn = FileStorageNode(file_path)
        self.assertEqual(
            sorted(list(fsn.items())),
            [
                ('bar', 'bar'),
                ('binary', b'Hello'),
                ('foo', 'foo'),
                ('none', ''),
                ('unset', ''),
                ('\xe4\xf6\xfc', '\xe4\xf6\xfc'),
            ],
        )
        lines = self._read_file(file_path)
        self.assertTrue('binary:b64:SGVsbG8=\n' in lines)

    def test_file_storage_ignores_malformed_lines(self):
        file_path = os.path.join(self.tempdir, 'filestorage')
        with open(file_path, 'w') as f:
            f.write('foo:foo\nmalformed\nbar:bar\n')
        fsn = FileStorageNode(file_path)
        self.assertEqual(list(fsn.items()), [('foo', 'foo'), ('bar', 'bar')])

    def test_file_storage_invalidate(self):
        file_path = os.path.join(self.tempdir, 'filestorage')
        fsn = FileStorageNode(file_path)
        fsn['foo'] = 'foo'
        fsn()
        fsn['bar'] = 'bar'
        fsn.invalidate()
        self.assertEqual(list(fsn.keys()), ['foo'])

    def test_principal_attributes_id_and_password(self):
        ugm = self._create_ugm()
        ugm()
        user = ugm.users.create('max', fullname='Max')
        ugm.users.passwd('max', None, 'secret')
        group = ugm.groups.create('group1')
        self.assertEqual(user.attrs['id'], 'max')
        self.assertEqual(user.attrs['password'], ugm.users.storage['max'])
        self.assertEqual(group.attrs['id'], 'group1')

    def test_group_getitem_non_member(self):
        ugm = self._create_ugm()
        ugm()
        ugm.users.create('max')
        group = ugm.groups.create('group1')
        with self.assertRaises(KeyError) as arc:
            group['max']
        self.assertEqual(str(arc.exception), "'max'")

    def test_ugm(self):
        ugm = self._create_ugm()

        expected = "<Ugm object 'ugm' at "
        self.assertTrue(str(ugm).startswith(expected))

        expected = "<Users object 'users' at "
        self.assertTrue(str(ugm.users).startswith(expected))

        expected = "<Groups object 'groups' at "
        self.assertTrue(str(ugm.groups).startswith(expected))

        expected = "<FileAttributes object '__attrs__' at"
        self.assertTrue(str(ugm.attrs).startswith(expected))
        self.assertTrue(str(ugm.roles_storage).startswith(expected))
        self.assertTrue(ugm.attrs is ugm.roles_storage)

        with self.assertRaises(KeyError) as arc:
            ugm['inexistent'] = ugm.users
        self.assertEqual(str(arc.exception), "'inexistent'")

        with self.assertRaises(NotImplementedError) as arc:
            del ugm['users']
        self.assertEqual(str(arc.exception), 'Operation forbidden on this node.')

        # Nothing created yet
        self.assertEqual(sorted(os.listdir(self.tempdir)), ['principal_data'])
        # Calling UGM persists
        ugm()
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['groups', 'principal_data', 'roles', 'users'],
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
        user = ugm.users.create('max', fullname='Max', email='foo@bar.com')
        expected = "<User object 'max' at "
        self.assertTrue(str(user).startswith(expected))
        self.assertEqual(
            ugm.treerepr(),
            (
                "<class 'node.ext.ugm.file.Ugm'>: ugm\n"
                "  <class 'node.ext.ugm.file.Users'>: users\n"
                "    <class 'node.ext.ugm.file.User'>: max\n"
                "  <class 'node.ext.ugm.file.Groups'>: groups\n"
            ),
        )

        # Nothing written yet
        lines = self._read_file(ugm.users.file_path)
        self.assertEqual(lines, [])

        self.checkOutput(
            """\
        /.../principal_data/users/max
        """,
            user.attrs.file_path,
        )

        with self.assertRaises(IOError) as arc:
            open(user.attrs.file_path)
        self.checkOutput(
            """\
        [Errno 2] No such file or directory: '/.../users/max'
        """,
            str(arc.exception),
        )

        # Persist and read related files again
        ugm()
        lines = self._read_file(ugm.users.file_path)
        self.assertEqual(lines, ['max:\n'])

        lines = self._read_file(user.attrs.file_path)
        self.assertEqual(sorted(lines), ['email:foo@bar.com\n', 'fullname:Max\n'])

        # Authentication is prohibited for users without a password
        self.assertFalse(ugm.users.authenticate('max', 'secret'))

        # Set Password for new User
        ugm.users.passwd('max', None, 'secret')
        ugm()
        lines = self._read_file(ugm.users.file_path)
        self.checkOutput(
            """\
        ['max:...\\n']
        """,
            str(lines),
        )

        # Password for inextistent user
        with self.assertRaises(ValueError) as arc:
            ugm.users.passwd('sepp', None, 'secret')
        self.assertEqual(str(arc.exception), "User with id 'sepp' does not exist.")

        # Password with wrong oldpw
        with self.assertRaises(ValueError) as arc:
            ugm.users.passwd('max', 'wrong', 'new')
        self.assertEqual(str(arc.exception), 'Old password does not match.')

        # Set new password for max
        ugm.users.passwd('max', 'secret', 'secret1')
        ugm()
        lines = self._read_file(ugm.users.file_path)
        self.checkOutput(
            """\
        ['max:...\\n']
        """,
            str(lines),
        )

        # Authentication
        self.assertFalse(ugm.users.authenticate('inexistent', 'secret'))
        self.assertFalse(ugm.users.authenticate('max', 'secret'))
        self.assertTrue(ugm.users.authenticate('max', 'secret1'))

        # Add another user
        user = ugm.users.create('sepp', fullname='Sepp', email='baz@bar.com')
        ugm.users.passwd('sepp', None, 'secret')
        ugm()
        self.assertEqual(
            ugm.treerepr(),
            (
                "<class 'node.ext.ugm.file.Ugm'>: ugm\n"
                "  <class 'node.ext.ugm.file.Users'>: users\n"
                "    <class 'node.ext.ugm.file.User'>: max\n"
                "    <class 'node.ext.ugm.file.User'>: sepp\n"
                "  <class 'node.ext.ugm.file.Groups'>: groups\n"
            ),
        )
        lines = self._read_file(ugm.users.file_path)
        self.checkOutput(
            """\
        ['max:...\\n',
        'sepp:...\\n']
        """,
            str(lines),
        )

        # ``__setitem__`` on user is prohibited
        with self.assertRaises(NotImplementedError) as arc:
            ugm.users['max']['foo'] = user
        self.assertEqual(str(arc.exception), 'User does not support ``__setitem__``')

        # Test expires
        user = ugm.users['max']
        self.assertFalse(user.expired)
        self.assertEqual(user.expires, None)
        user.expires = datetime.now()
        self.assertEqual(user.expires, None)

        ugm.user_expires_attr = 'expires'
        self.assertFalse(user.expired)
        with self.assertRaises(ValueError):
            user.expires = 'expires'

        user.expires = None
        self.assertEqual(user.attrs['expires'], '')
        self.assertFalse(user.expired)

        user.expires = datetime.now() + timedelta(1)
        self.assertTrue(len(user.attrs['expires']) > -1)
        self.assertFalse(user.expired)
        self.assertTrue(user.authenticate('secret1'))
        self.assertTrue(ugm.users.authenticate('max', 'secret1'))

        user.expires = datetime.now()
        self.assertTrue(user.expired)
        self.assertFalse(user.authenticate('secret1'))
        self.assertFalse(ugm.users.authenticate('max', 'secret1'))

    def test_group(self):
        ugm = self._create_ugm()
        ugm()

        # Add users
        ugm.users.create('max', fullname='Max', email='foo@bar.com')
        ugm.users.create('sepp', fullname='Sepp', email='baz@bar.com')

        # Add new Group
        group = ugm.groups.create('group1', description='Group 1')
        expected = "<Group object 'group1' at "
        self.assertTrue(str(group).startswith(expected))
        self.assertEqual(
            ugm.treerepr(),
            (
                "<class 'node.ext.ugm.file.Ugm'>: ugm\n"
                "  <class 'node.ext.ugm.file.Users'>: users\n"
                "    <class 'node.ext.ugm.file.User'>: max\n"
                "    <class 'node.ext.ugm.file.User'>: sepp\n"
                "  <class 'node.ext.ugm.file.Groups'>: groups\n"
                "    <class 'node.ext.ugm.file.Group'>: group1\n"
            ),
        )

        # Nothing written yet
        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(lines, [])

        self.checkOutput(
            """\
        /.../principal_data/groups/group1
        """,
            group.attrs.file_path,
        )

        with self.assertRaises(IOError) as arc:
            open(group.attrs.file_path)
        self.checkOutput(
            """\
        [Errno 2] No such file or directory: '/.../groups/group1'
        """,
            str(arc.exception),
        )

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
        self.assertEqual(str(arc.exception), 'Group does not support ``__setitem__``')

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
        group = ugm.groups.create('group2', description='Group 2')
        expected = "<Group object 'group2' at "
        self.assertTrue(str(group).startswith(expected))
        group.add('max')
        group.add('sepp')
        self.assertEqual(
            ugm.treerepr(),
            (
                "<class 'node.ext.ugm.file.Ugm'>: ugm\n"
                "  <class 'node.ext.ugm.file.Users'>: users\n"
                "    <class 'node.ext.ugm.file.User'>: max\n"
                "    <class 'node.ext.ugm.file.User'>: sepp\n"
                "  <class 'node.ext.ugm.file.Groups'>: groups\n"
                "    <class 'node.ext.ugm.file.Group'>: group1\n"
                "      <class 'node.ext.ugm.file.User'>: max\n"
                "    <class 'node.ext.ugm.file.Group'>: group2\n"
                "      <class 'node.ext.ugm.file.User'>: max\n"
                "      <class 'node.ext.ugm.file.User'>: sepp\n"
            ),
        )

        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(lines, ['group1:max\n'])

        ugm()
        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(lines, ['group1:max\n', 'group2:max,sepp\n'])

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
        self.assertEqual(sorted(users.keys()), ['123sepp', 'max', 'maxii', 'sepp'])

        # Test Search on users
        self.assertEqual(sorted(users.search()), ['123sepp', 'max', 'maxii', 'sepp'])
        self.assertEqual(
            sorted(users.search(criteria=dict())), ['123sepp', 'max', 'maxii', 'sepp']
        )
        self.assertEqual(users.search(criteria=dict(id='max')), ['max'])
        self.assertEqual(sorted(users.search(criteria=dict(id='max*'))), ['max', 'maxii'])
        self.assertEqual(users.search(criteria=dict(id='sepp')), ['sepp'])
        self.assertEqual(
            sorted(users.search(criteria=dict(id='*sep*'))), ['123sepp', 'sepp']
        )

        # Search on users exact match
        self.assertEqual(users.search(criteria=dict(id='max'), exact_match=True), ['max'])

        with self.assertRaises(ValueError) as arc:
            users.search(criteria=dict(id='max*'), exact_match=True)
        self.assertEqual(str(arc.exception), 'Exact match asked but result not unique')

        with self.assertRaises(ValueError) as arc:
            users.search(criteria=dict(id='inexistent'), exact_match=True)
        self.assertEqual(
            str(arc.exception), 'Exact match asked but result length is zero'
        )

        # Search on users attribute list
        res = users.search(criteria=dict(id='max'), attrlist=['fullname', 'email'])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][0], 'max')
        self.assertEqual(res[0][1], {'email': 'foo@bar.com', 'fullname': 'Max Muster'})

        res = sorted(
            users.search(criteria=dict(id='max*'), attrlist=['fullname', 'email'])
        )
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0][0], 'max')
        self.assertEqual(res[0][1], {'email': 'foo@bar.com', 'fullname': 'Max Muster'})
        self.assertEqual(res[1][0], 'maxii')
        self.assertEqual(res[1][1], {'email': '', 'fullname': ''})

        res = sorted(users.search(criteria=dict(id='*ax*'), attrlist=['id']))
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0][0], 'max')
        self.assertEqual(res[0][1], {'id': 'max'})
        self.assertEqual(res[1][0], 'maxii')
        self.assertEqual(res[1][1], {'id': 'maxii'})

        # Search on users or search
        res = sorted(
            users.search(criteria=dict(fullname='*Muster*', id='max*'), or_search=True)
        )
        self.assertEqual(res, ['max', 'maxii', 'sepp'])

        res = users.search(criteria=dict(fullname='*Muster*', id='max*'), or_search=False)
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
            ['group1', 'group2', 'group3'],
        )
        self.assertEqual(
            sorted(groups.search(criteria=dict(id='*rou*'))),
            ['group1', 'group2', 'group3'],
        )
        self.assertEqual(groups.search(criteria=dict(id='*3')), ['group3'])

        # Search on groups exact match
        self.assertEqual(
            groups.search(criteria=dict(id='group1'), exact_match=True), ['group1']
        )

        with self.assertRaises(ValueError) as arc:
            groups.search(criteria=dict(id='group*'), exact_match=True)
        self.assertEqual(str(arc.exception), 'Exact match asked but result not unique')

        with self.assertRaises(ValueError) as arc:
            groups.search(criteria=dict(id='inexistent'), exact_match=True)
        self.assertEqual(
            str(arc.exception), 'Exact match asked but result length is zero'
        )

        # Search on groups attribute list
        res = sorted(groups.search(criteria=dict(id='group*'), attrlist=['description']))
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0][0], 'group1')
        self.assertEqual(res[0][1], {'description': 'Group 1 Description'})
        self.assertEqual(res[1][0], 'group2')
        self.assertEqual(res[1][1], {'description': 'Group 2 Description'})
        self.assertEqual(res[2][0], 'group3')
        self.assertEqual(res[2][1], {'description': ''})

        res = groups.search(criteria=dict(id='*2'), attrlist=['id', 'description'])
        self.assertEqual(
            res, [('group2', {'id': 'group2', 'description': 'Group 2 Description'})]
        )

        # Search on groups or search
        res = sorted(
            groups.search(criteria=dict(description='*Desc*', id='*g*'), or_search=True)
        )
        self.assertEqual(res, ['group1', 'group2', 'group3'])

        res = groups.search(criteria=dict(description='*Desc*', id='*1'), or_search=False)
        self.assertEqual(res, ['group1'])

        res = groups.search(criteria=dict(description='*Desc*', id='*3'), or_search=False)
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
        self.assertEqual(
            ugm.treerepr(),
            (
                "<class 'node.ext.ugm.file.Ugm'>: ugm\n"
                "  <class 'node.ext.ugm.file.Users'>: users\n"
                "    <class 'node.ext.ugm.file.User'>: max\n"
                "    <class 'node.ext.ugm.file.User'>: sepp\n"
                "  <class 'node.ext.ugm.file.Groups'>: groups\n"
                "    <class 'node.ext.ugm.file.Group'>: group1\n"
                "      <class 'node.ext.ugm.file.User'>: max\n"
                "    <class 'node.ext.ugm.file.Group'>: group2\n"
                "      <class 'node.ext.ugm.file.User'>: max\n"
                "      <class 'node.ext.ugm.file.User'>: sepp\n"
            ),
        )

        # Delete user from group
        with self.assertRaises(KeyError) as arc:
            del ugm.groups['group2']['inexistent']
        self.assertEqual(str(arc.exception), "'inexistent'")

        del ugm.groups['group2']['max']
        self.assertEqual(
            ugm.groups.treerepr(),
            (
                "<class 'node.ext.ugm.file.Groups'>: groups\n"
                "  <class 'node.ext.ugm.file.Group'>: group1\n"
                "    <class 'node.ext.ugm.file.User'>: max\n"
                "  <class 'node.ext.ugm.file.Group'>: group2\n"
                "    <class 'node.ext.ugm.file.User'>: sepp\n"
            ),
        )

        # Not persisted yet
        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(sorted(lines), ['group1:max\n', 'group2:max,sepp\n'])

        # Call tree and check result
        ugm()
        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(sorted(lines), ['group1:max\n', 'group2:sepp\n'])

    def test_user_roles(self):
        ugm = self._create_ugm()
        ugm.users.create('max', fullname='Max Muster', email='foo@bar.com')
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
        self.assertEqual(str(arc.exception), "Principal already has role 'manager'")

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
        self.assertEqual(str(arc.exception), "Principal does not has role 'supervisor'")

        # Call persists
        user()
        lines = self._read_file(ugm.roles_file)
        self.assertEqual(lines, ['max::manager\n'])

    def test_group_roles(self):
        ugm = self._create_ugm()
        ugm.users.create('max')
        ugm.groups.create('group1', description='Group 1 Description')
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
        self.assertEqual(str(arc.exception), "Principal already has role 'authenticated'")

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
        self.assertEqual(str(arc.exception), "Principal does not has role 'editor'")

        # Call persists
        group()
        lines = self._read_file(ugm.roles_file)
        self.assertEqual(lines, ['group:group1::authenticated\n'])

    def test_users(self):
        ugm = self._create_ugm()
        ugm.users.create('max', fullname='Max Muster', email='foo@bar.com')
        ugm.users['max'].add_role('manager')
        ugm.groups.create('group1', description='Group 1 Description')
        ugm.groups.create('group2', description='Group 2 Description')
        ugm.groups['group1'].add('max')
        ugm.groups['group2'].add('max')
        ugm()

        lines = self._read_file(ugm.users.file_path)
        self.assertEqual(sorted(lines), ['max:\n'])

        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(sorted(lines), ['group1:max\n', 'group2:max\n'])

        lines = self._read_file(ugm.roles_file)
        self.assertEqual(sorted(lines), ['max::manager\n'])

        self.assertEqual(os.listdir(os.path.join(ugm.data_directory, 'users')), ['max'])

        # Recreate ugm object
        ugm = self._create_ugm()

        # XXX: id_for_login actually just returns given login name
        self.assertEqual(ugm.users.id_for_login('max'), 'max')

        with self.assertRaises(KeyError) as arc:
            ugm.users['inexistent']
        self.assertEqual(str(arc.exception), "'inexistent'")

        expected = "<User object 'max' at "
        self.assertTrue(str(ugm.users['max']).startswith(expected))

        # Delete user. User gets removed from groups and roles
        del ugm.users['max']
        self.assertEqual(
            ugm.treerepr(),
            (
                "<class 'node.ext.ugm.file.Ugm'>: ugm\n"
                "  <class 'node.ext.ugm.file.Users'>: users\n"
                "  <class 'node.ext.ugm.file.Groups'>: groups\n"
                "    <class 'node.ext.ugm.file.Group'>: group1\n"
                "    <class 'node.ext.ugm.file.Group'>: group2\n"
            ),
        )
        ugm.users()

        lines = self._read_file(ugm.users.file_path)
        self.assertEqual(sorted(lines), [])

        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(sorted(lines), ['group1:\n', 'group2:\n'])

        lines = self._read_file(ugm.roles_file)
        self.assertEqual(sorted(lines), [])

        # User data is deleted as well
        self.assertEqual(os.listdir(os.path.join(ugm.data_directory, 'users')), [])

    def test_groups(self):
        ugm = self._create_ugm()
        ugm.users.create('max', fullname='Max Muster', email='foo@bar.com')
        ugm.groups.create('group1', description='Group 1 Description')
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
            os.listdir(os.path.join(ugm.data_directory, 'groups')), ['group1']
        )

        # Recreate ugm object
        ugm = self._create_ugm()

        with self.assertRaises(KeyError) as arc:
            ugm.groups['inexistent']
        self.assertEqual(str(arc.exception), "'inexistent'")

        with self.assertRaises(KeyError) as arc:
            ugm.groups['group1'].add('inexistent')
        self.assertEqual(str(arc.exception), "'inexistent'")

        expected = "<Group object 'group1' at "
        self.assertTrue(str(ugm.groups['group1']).startswith(expected))

        # Delete group. Group gets removed from user and from roles
        del ugm.groups['group1']
        self.assertEqual(
            ugm.treerepr(),
            (
                "<class 'node.ext.ugm.file.Ugm'>: ugm\n"
                "  <class 'node.ext.ugm.file.Users'>: users\n"
                "    <class 'node.ext.ugm.file.User'>: max\n"
                "  <class 'node.ext.ugm.file.Groups'>: groups\n"
            ),
        )
        self.assertEqual(ugm.users['max'].groups, [])
        ugm.groups()

        lines = self._read_file(ugm.users.file_path)
        self.assertEqual(sorted(lines), ['max:\n'])

        lines = self._read_file(ugm.groups.file_path)
        self.assertEqual(sorted(lines), [])

        lines = self._read_file(ugm.roles_file)
        self.assertEqual(sorted(lines), [])

        # Group data is deleted as well
        self.assertEqual(os.listdir(os.path.join(ugm.data_directory, 'groups')), [])

    # password storage

    def _ugm_with_stored_password(self, stored, name='max'):
        users_file = os.path.join(self.tempdir, 'users')
        with open(users_file, 'w') as f:
            f.write(f'{name}:{stored}\n')
        return Ugm(
            name='ugm',
            users_file=users_file,
            groups_file=os.path.join(self.tempdir, 'groups'),
            roles_file=os.path.join(self.tempdir, 'roles'),
            data_directory=os.path.join(self.tempdir, 'data'),
        )

    def _stored_password(self, name='max'):
        users_file = os.path.join(self.tempdir, 'users')
        for line in self._read_file(users_file):
            key, value = line.rstrip('\n').split(':', 1)
            if key == name:
                return value

    def test_passwd_stores_current_format(self):
        ugm = self._ugm_with_stored_password('')
        ugm.users.passwd('max', None, 'secret')
        self.assertTrue(self._stored_password().startswith('$scrypt$'))
        self.assertTrue(ugm.users.authenticate('max', 'secret'))

    def test_passwd_checks_old_password_of_former_format(self):
        ugm = self._ugm_with_stored_password(legacy_hash('secret'))
        with self.assertRaises(ValueError):
            ugm.users.passwd('max', 'wrong', 'new')
        ugm.users.passwd('max', 'secret', 'new')
        self.assertTrue(ugm.users.authenticate('max', 'new'))

    def test_login_replaces_hash_of_former_format(self):
        for stored in (legacy_hash('secret'), wrap_legacy_hash(legacy_hash('secret'))):
            with self.subTest(stored=stored[:16]):
                ugm = self._ugm_with_stored_password(stored)
                self.assertTrue(ugm.users.authenticate('max', 'secret'))
                self.assertTrue(self._stored_password().startswith('$scrypt$'))
                self.assertTrue(check_password('secret', self._stored_password()))
                self.assertTrue(ugm.users.authenticate('max', 'secret'))

    def test_failed_login_keeps_hash_of_former_format(self):
        stored = legacy_hash('secret')
        ugm = self._ugm_with_stored_password(stored)
        self.assertFalse(ugm.users.authenticate('max', 'wrong'))
        self.assertEqual(self._stored_password(), stored)

    def test_login_with_current_format_writes_nothing(self):
        ugm = self._ugm_with_stored_password(hash_password('secret'))
        with mock.patch.object(type(ugm.users), 'write_file') as write_file:
            self.assertTrue(ugm.users.authenticate('max', 'secret'))
        write_file.assert_not_called()

    def test_login_survives_failing_rehash(self):
        ugm = self._ugm_with_stored_password(legacy_hash('secret'))
        with mock.patch.object(
            type(ugm.users), 'write_file', side_effect=OSError('full')
        ):
            with self.assertLogs('node.ext.ugm', level='ERROR'):
                self.assertTrue(ugm.users.authenticate('max', 'secret'))

    def test_rejected_login_spends_the_time_of_a_check(self):
        ugm = self._ugm_with_stored_password('')
        with mock.patch.object(
            file_module, 'reject_password', return_value=False
        ) as reject:
            self.assertFalse(ugm.users.authenticate('inexistent', 'secret'))
            self.assertFalse(ugm.users.authenticate('max', 'secret'))
        self.assertEqual(reject.call_count, 2)

    def test_expired_user_spends_the_time_of_a_check(self):
        ugm = self._ugm_with_stored_password(hash_password('secret'))
        ugm.user_expires_attr = 'expires'
        ugm.users['max'].expires = datetime.now() - timedelta(days=1)
        with mock.patch.object(
            file_module, 'reject_password', return_value=False
        ) as reject:
            self.assertFalse(ugm.users.authenticate('max', 'secret'))
        reject.assert_called_once_with('secret')

    def test_authenticate_without_credentials(self):
        ugm = self._ugm_with_stored_password(hash_password('secret'))
        with mock.patch.object(file_module, 'reject_password') as reject:
            self.assertFalse(ugm.users.authenticate('max', None))
            self.assertFalse(ugm.users.authenticate('max', ''))
            self.assertFalse(ugm.users.authenticate(None, 'secret'))
        reject.assert_not_called()

    def test_write_file_replaces_file_at_once(self):
        ugm = self._ugm_with_stored_password('before')
        ugm.users.storage['max'] = 'after'
        with mock.patch.object(file_module.os, 'replace', side_effect=OSError('full')):
            with self.assertRaises(OSError):
                ugm.users.write_file()
        self.assertEqual(self._stored_password(), 'before')
        self.assertEqual(os.listdir(self.tempdir), ['users'])

    def test_write_file_keeps_file_mode(self):
        ugm = self._ugm_with_stored_password('before')
        users_file = os.path.join(self.tempdir, 'users')
        os.chmod(users_file, 0o600)
        ugm.users.storage['max'] = 'after'
        ugm.users.write_file()
        self.assertEqual(self._stored_password(), 'after')
        self.assertEqual(stat.S_IMODE(os.stat(users_file).st_mode), 0o600)
        self.assertEqual(os.listdir(self.tempdir), ['users'])

    def test_wrap_passwords(self):
        users_file = os.path.join(self.tempdir, 'users')
        current = hash_password('other')
        with open(users_file, 'w') as f:
            f.write(f'max:{legacy_hash("secret")}\n')
            f.write(f'sepp:{current}\n')
            f.write('empty:\n')
        with mock.patch('builtins.print') as print_:
            self.assertEqual(wrap_passwords([users_file]), 0)
        print_.assert_called_once_with('1 of 3 passwords wrapped.')
        self.assertTrue(self._stored_password('max').startswith('$scrypt-sha256$'))
        self.assertTrue(check_password('secret', self._stored_password('max')))
        self.assertEqual(self._stored_password('sepp'), current)
        self.assertEqual(self._stored_password('empty'), '')

        # a second run finds nothing to do
        wrapped = self._stored_password('max')
        with mock.patch('builtins.print') as print_:
            self.assertEqual(wrap_passwords([users_file]), 0)
        print_.assert_called_once_with('0 of 3 passwords wrapped.')
        self.assertEqual(self._stored_password('max'), wrapped)

    def test_wrap_passwords_reports_malformed_values(self):
        users_file = os.path.join(self.tempdir, 'users')
        with open(users_file, 'w') as f:
            f.write('broken:not base64!\n')
            f.write(f'max:{legacy_hash("secret")}\n')
        with mock.patch('builtins.print') as print_:
            self.assertEqual(wrap_passwords([users_file]), 1)
        print_.assert_any_call('1 of 2 passwords wrapped.')
        print_.assert_any_call('Malformed, left as they are: broken')
        self.assertEqual(self._stored_password('broken'), 'not base64!')

    def test_wrap_passwords_usage(self):
        with mock.patch('builtins.print') as print_:
            self.assertEqual(wrap_passwords([]), 2)
            self.assertEqual(wrap_passwords([os.path.join(self.tempdir, 'missing')]), 2)
        self.assertEqual(print_.call_count, 2)
