from node.behaviors import Adopt
from node.behaviors import Attributes
from node.behaviors import DefaultInit
from node.behaviors import DictStorage
from node.behaviors import NodeChildValidate
from node.behaviors import Nodespaces
from node.behaviors import Nodify
from node.behaviors import OdictStorage
from node.ext.ugm import Group
from node.ext.ugm import Groups
from node.ext.ugm import Principal
from node.ext.ugm import Principals
from node.ext.ugm import Ugm
from node.ext.ugm import User
from node.ext.ugm import Users
from node.ext.ugm.interfaces import IGroup
from node.ext.ugm.interfaces import IGroups
from node.ext.ugm.interfaces import IPrincipal
from node.ext.ugm.interfaces import IPrincipals
from node.ext.ugm.interfaces import IUgm
from node.ext.ugm.interfaces import IUser
from node.ext.ugm.interfaces import IUsers
from node.tests import NodeTestCase
from plumber import plumbing


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
    Principal,
    DictStorage)
class PrincipalNode(object):
    """Abstract principal.
    """


@plumbing(
    NodeChildValidate,
    Nodespaces,
    Adopt,
    Attributes,
    DefaultInit,
    Nodify,
    User,
    DictStorage)
class UserNode(object):
    """Abstract user.
    """


@plumbing(
    NodeChildValidate,
    Nodespaces,
    Adopt,
    Attributes,
    DefaultInit,
    Nodify,
    Group,
    DictStorage)
class GroupNode(object):
    """Abstract group.
    """


@plumbing(
    NodeChildValidate,
    Nodespaces,
    Adopt,
    Attributes,
    DefaultInit,
    Nodify,
    Principals,
    OdictStorage)
class PrincipalsNode(object):
    """Abstract principals.
    """


@plumbing(
    NodeChildValidate,
    Nodespaces,
    Adopt,
    Attributes,
    DefaultInit,
    Nodify,
    Users,
    OdictStorage)
class UsersNode(object):
    """Abstract users.
    """


@plumbing(
    NodeChildValidate,
    Nodespaces,
    Adopt,
    Attributes,
    DefaultInit,
    Nodify,
    Groups,
    OdictStorage)
class GroupsNode(object):
    """Abstract groups.
    """


@plumbing(
    NodeChildValidate,
    Nodespaces,
    Adopt,
    Attributes,
    Nodify,
    Ugm,
    OdictStorage)
class UgmNode(object):
    """Abstract ugm.
    """

    def __init__(self, name, users, groups):
        self.__name__ = name
        self['users'] = users
        self['groups'] = groups

    @property
    def users(self):
        return self['users']

    @property
    def groups(self):
        return self['groups']

    @property
    def roles_storage(self):
        return lambda: None


###############################################################################
# Tests
###############################################################################

class TestAPI(NodeTestCase):

    def test_abstract_principal(self):
        principal = PrincipalNode(name='someprincipal')
        expected = '<PrincipalNode object \'someprincipal\' at '
        self.assertTrue(str(principal).startswith(expected))
        self.assertTrue(IPrincipal.providedBy(principal))
        self.assertEqual([key for key in principal], [])

        # ``add_role``, ``remove_role``, ``roles`` and ``__call__`` is not
        # implemented on abstract principal
        err = self.expect_error(
            NotImplementedError,
            principal.add_role,
            'role'
        )
        expected = 'Abstract ``Principal`` does not implement ``add_role``'
        self.assertEqual(str(err), expected)

        err = self.expect_error(
            NotImplementedError,
            principal.remove_role,
            'role'
        )
        expected = 'Abstract ``Principal`` does not implement ``remove_role``'
        self.assertEqual(str(err), expected)

        err = self.expect_error(NotImplementedError, lambda: principal.roles)
        expected = 'Abstract ``Principal`` does not implement ``roles``'
        self.assertEqual(str(err), expected)

        def __call__fails():
            principal()
        err = self.expect_error(NotImplementedError, __call__fails)
        expected = 'Abstract ``Principal`` does not implement ``__call__``'
        self.assertEqual(str(err), expected)

    def test_abstract_user(self):
        user = UserNode(name='someuser')
        expected = '<UserNode object \'someuser\' at '
        self.assertTrue(str(user).startswith(expected))
        self.assertTrue(IUser.providedBy(user))
        self.assertEqual(user.login, 'someuser')

        user.attrs['login'] = 'foo@bar.baz'
        self.assertEqual(user.login, 'foo@bar.baz')

        def __getitem__fails():
            user['foo']
        err = self.expect_error(NotImplementedError, __getitem__fails)
        expected = 'User does not support ``__getitem__``'
        self.assertEqual(str(err), expected)

        def __setitem__fails():
            user['foo'] = UserNode()
        err = self.expect_error(NotImplementedError, __setitem__fails)
        expected = 'User does not support ``__setitem__``'
        self.assertEqual(str(err), expected)

        def __delitem__fails():
            del user['foo']
        err = self.expect_error(NotImplementedError, __delitem__fails)
        expected = 'User does not support ``__delitem__``'
        self.assertEqual(str(err), expected)

        self.assertEqual([x for x in user], [])

        # ``authenticate`` and ``passwd`` gets delegated to parent. Fails
        # since User is not contained in Users container
        err = self.expect_error(AttributeError, user.authenticate, 'secret')
        expected = '\'NoneType\' object has no attribute \'authenticate\''
        self.assertEqual(str(err), expected)

        err = self.expect_error(AttributeError, user.passwd, 'old', 'new')
        expected = '\'NoneType\' object has no attribute \'passwd\''
        self.assertEqual(str(err), expected)

        # ``groups`` is not implemented in abstract base behavior
        err = self.expect_error(NotImplementedError, lambda: user.groups)
        expected = 'Abstract ``User`` does not implement ``groups``'
        self.assertEqual(str(err), expected)

        # ``group_ids`` is not implemented in abstract base behavior
        err = self.expect_error(NotImplementedError, lambda: user.group_ids)
        expected = 'Abstract ``User`` does not implement ``group_ids``'
        self.assertEqual(str(err), expected)

    def test_abstract_group(self):
        group = GroupNode(name='somegroup')
        expected = '<GroupNode object \'somegroup\' at '
        self.assertTrue(str(group).startswith(expected))
        self.assertTrue(IGroup.providedBy(group))

        # ``users`` and ``member_ids`` is not implemented in abstract base
        # behavior
        err = self.expect_error(NotImplementedError, lambda: group.users)
        expected = 'Abstract ``Group`` does not implement ``users``'
        self.assertEqual(str(err), expected)

        err = self.expect_error(NotImplementedError, lambda: group.member_ids)
        expected = 'Abstract ``Group`` does not implement ``member_ids``'
        self.assertEqual(str(err), expected)

        err = self.expect_error(NotImplementedError, group.add, 'foo')
        expected = 'Abstract ``Group`` does not implement ``add``'
        self.assertEqual(str(err), expected)

        def __setitem__fails():
            group['foo'] = GroupNode()
        err = self.expect_error(NotImplementedError, __setitem__fails)
        expected = 'Group does not support ``__setitem__``'
        self.assertEqual(str(err), expected)

    def test_abstract_principals(self):
        principals = PrincipalsNode(name='principals')
        expected = '<PrincipalsNode object \'principals\' at '
        self.assertTrue(str(principals).startswith(expected))
        self.assertTrue(IPrincipals.providedBy(principals))
        self.assertEqual(principals.ids, [])

        # ``search`` ,``create`` and ``__call__`` are not implemented in
        # abstract base behavior
        err = self.expect_error(NotImplementedError, principals.search)
        expected = 'Abstract ``Principals`` does not implement ``search``'
        self.assertEqual(str(err), expected)

        err = self.expect_error(NotImplementedError, principals.create, 'foo')
        expected = 'Abstract ``Principals`` does not implement ``create``'
        self.assertEqual(str(err), expected)

        def __call__fails():
            principals()
        err = self.expect_error(NotImplementedError, __call__fails)
        expected = 'Abstract ``Principals`` does not implement ``__call__``'
        self.assertEqual(str(err), expected)

    def test_abstract_users(self):
        users = UsersNode(name='users')
        expected = '<UsersNode object \'users\' at '
        self.assertTrue(str(users).startswith(expected))
        self.assertTrue(IUsers.providedBy(users))

        err = self.expect_error(NotImplementedError, users.id_for_login, 'foo')
        expected = 'Abstract ``Users`` does not implement ``id_for_login``'
        self.assertEqual(str(err), expected)

        # Add user
        user = users['someuser'] = UserNode()
        self.assertEqual(users.treerepr(), (
            '<class \'node.ext.ugm.tests.test_api.UsersNode\'>: users\n'
            '  <class \'node.ext.ugm.tests.test_api.UserNode\'>: someuser\n'
        ))
        self.assertEqual(users.ids, ['someuser'])

        # Abstract users behavior does not implement ``authenticate`` and
        # ``passwd``
        err = self.expect_error(
            NotImplementedError,
            user.authenticate,
            'secret'
        )
        expected = 'Abstract ``Users`` does not implement ``authenticate``'
        self.assertEqual(str(err), expected)

        err = self.expect_error(NotImplementedError, user.passwd, 'old', 'new')
        expected = 'Abstract ``Users`` does not implement ``passwd``'
        self.assertEqual(str(err), expected)

    def test_abstract_groups(self):
        groups = GroupsNode(name='groups')
        expected = '<GroupsNode object \'groups\' at '
        self.assertTrue(str(groups).startswith(expected))
        self.assertTrue(IGroups.providedBy(groups))

    def test_abstract_ugm(self):
        users = UsersNode(name='users')
        groups = GroupsNode(name='groups')
        ugm = UgmNode('ugm', users, groups)
        expected = '<UgmNode object \'ugm\' at '
        self.assertTrue(str(ugm).startswith(expected))
        self.assertTrue(IUgm.providedBy(ugm))

        expected = '<UsersNode object \'users\' at '
        self.assertTrue(str(ugm.users).startswith(expected))

        expected = '<GroupsNode object \'groups\' at '
        self.assertTrue(str(ugm.groups).startswith(expected))

        self.check_output("""\
        <function ...<lambda> at ...>
        """, str(ugm.roles_storage))

        # Abstract ugm behavior does not implement ``add_role``,
        # ``remove_role``, ``roles`` and ``__call__``
        user = users['someuser'] = UserNode()
        err = self.expect_error(
            NotImplementedError,
            ugm.add_role,
            'role',
            user
        )
        expected = 'Abstract ``Ugm`` does not implement ``add_role``'
        self.assertEqual(str(err), expected)

        err = self.expect_error(
            NotImplementedError,
            ugm.remove_role,
            'role',
            user
        )
        expected = 'Abstract ``Ugm`` does not implement ``remove_role``'
        self.assertEqual(str(err), expected)

        err = self.expect_error(NotImplementedError, ugm.roles, user)
        expected = 'Abstract ``Ugm`` does not implement ``roles``'
        self.assertEqual(str(err), expected)

        def __call__fails():
            ugm()
        err = self.expect_error(NotImplementedError, __call__fails)
        expected = 'Abstract ``Ugm`` does not implement ``__call__``'
        self.assertEqual(str(err), expected)
