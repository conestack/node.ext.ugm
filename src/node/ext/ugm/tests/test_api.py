from node.behaviors import Attributes
from node.behaviors import DefaultInit
from node.behaviors import DictStorage
from node.behaviors import MappingAdopt
from node.behaviors import MappingConstraints
from node.behaviors import MappingNode
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
    MappingConstraints,
    MappingAdopt,
    Attributes,
    DefaultInit,
    MappingNode,
    Principal,
    DictStorage)
class PrincipalNode(object):
    """Abstract principal.
    """


@plumbing(
    MappingConstraints,
    MappingAdopt,
    Attributes,
    DefaultInit,
    MappingNode,
    User,
    DictStorage)
class UserNode(object):
    """Abstract user.
    """


@plumbing(
    MappingConstraints,
    MappingAdopt,
    Attributes,
    DefaultInit,
    Group,
    MappingNode)
class GroupNode(object):
    """Abstract group.
    """


@plumbing(
    MappingConstraints,
    MappingAdopt,
    Attributes,
    DefaultInit,
    MappingNode,
    Principals,
    OdictStorage)
class PrincipalsNode(object):
    """Abstract principals.
    """


@plumbing(
    MappingConstraints,
    MappingAdopt,
    Attributes,
    DefaultInit,
    MappingNode,
    Users,
    OdictStorage)
class UsersNode(object):
    """Abstract users.
    """


@plumbing(
    MappingConstraints,
    MappingAdopt,
    Attributes,
    DefaultInit,
    MappingNode,
    Groups,
    OdictStorage)
class GroupsNode(object):
    """Abstract groups.
    """


@plumbing(
    MappingConstraints,
    MappingAdopt,
    Attributes,
    MappingNode,
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
        with self.assertRaises(NotImplementedError) as arc:
            principal.add_role('role')
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Principal`` does not implement ``add_role``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            principal.remove_role('role')
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Principal`` does not implement ``remove_role``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            principal.roles
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Principal`` does not implement ``roles``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            principal()
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Principal`` does not implement ``__call__``'
        )

    def test_abstract_user(self):
        user = UserNode(name='someuser')
        expected = '<UserNode object \'someuser\' at '
        self.assertTrue(str(user).startswith(expected))
        self.assertTrue(IUser.providedBy(user))
        self.assertEqual(user.login, 'someuser')

        user.attrs['login'] = 'foo@bar.baz'
        self.assertEqual(user.login, 'foo@bar.baz')

        with self.assertRaises(NotImplementedError) as arc:
            user['foo']
        self.assertEqual(
            str(arc.exception),
            'User does not support ``__getitem__``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            user['foo'] = UserNode()
        self.assertEqual(
            str(arc.exception),
            'User does not support ``__setitem__``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            del user['foo']
        self.assertEqual(
            str(arc.exception),
            'User does not support ``__delitem__``'
        )

        self.assertEqual([x for x in user], [])

        # ``authenticate`` and ``passwd`` gets delegated to parent. Fails
        # since User is not contained in Users container
        with self.assertRaises(AttributeError) as arc:
            user.authenticate('secret')
        self.assertEqual(
            str(arc.exception),
            '\'NoneType\' object has no attribute \'authenticate\''
        )

        with self.assertRaises(AttributeError) as arc:
            user.passwd('old', 'new')
        self.assertEqual(
            str(arc.exception),
            '\'NoneType\' object has no attribute \'passwd\''
        )

        # ``groups`` is not implemented in abstract base behavior
        with self.assertRaises(NotImplementedError) as arc:
            user.groups
        self.assertEqual(
            str(arc.exception),
            'Abstract ``User`` does not implement ``groups``'
        )

        # ``group_ids`` is not implemented in abstract base behavior
        with self.assertRaises(NotImplementedError) as arc:
            user.group_ids
        self.assertEqual(
            str(arc.exception),
            'Abstract ``User`` does not implement ``group_ids``'
        )

    def test_abstract_group(self):
        group = GroupNode(name='somegroup')
        expected = '<GroupNode object \'somegroup\' at '
        self.assertTrue(str(group).startswith(expected))
        self.assertTrue(IGroup.providedBy(group))

        # ``users`` and ``member_ids`` is not implemented in abstract base
        # behavior
        with self.assertRaises(NotImplementedError) as arc:
            group.users
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Group`` does not implement ``users``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            group.member_ids
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Group`` does not implement ``member_ids``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            group.add('foo')
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Group`` does not implement ``add``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            group['foo'] = GroupNode()
        self.assertEqual(
            str(arc.exception),
            'Group does not support ``__setitem__``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            group['foo']
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Group`` does not implement ``__getitem__``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            del group['foo']
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Group`` does not implement ``__delitem__``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            [x for x in group]
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Group`` does not implement ``__iter__``'
        )

    def test_abstract_principals(self):
        principals = PrincipalsNode(name='principals')
        expected = '<PrincipalsNode object \'principals\' at '
        self.assertTrue(str(principals).startswith(expected))
        self.assertTrue(IPrincipals.providedBy(principals))
        self.assertEqual(principals.ids, [])

        # ``search`` ,``create`` and ``__call__`` are not implemented in
        # abstract base behavior
        with self.assertRaises(NotImplementedError) as arc:
            principals.search()
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Principals`` does not implement ``search``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            principals.create('foo')
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Principals`` does not implement ``create``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            principals()
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Principals`` does not implement ``__call__``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            principals.invalidate()
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Principals`` does not implement ``invalidate``'
        )

    def test_abstract_users(self):
        users = UsersNode(name='users')
        expected = '<UsersNode object \'users\' at '
        self.assertTrue(str(users).startswith(expected))
        self.assertTrue(IUsers.providedBy(users))

        with self.assertRaises(NotImplementedError) as arc:
            users.id_for_login('foo')
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Users`` does not implement ``id_for_login``'
        )

        # Add user
        user = users['someuser'] = UserNode()
        self.assertEqual(users.treerepr(), (
            '<class \'node.ext.ugm.tests.test_api.UsersNode\'>: users\n'
            '  <class \'node.ext.ugm.tests.test_api.UserNode\'>: someuser\n'
        ))
        self.assertEqual(users.ids, ['someuser'])

        # Abstract users behavior does not implement ``authenticate`` and
        # ``passwd``
        with self.assertRaises(NotImplementedError) as arc:
            user.authenticate('secret')
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Users`` does not implement ``authenticate``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            user.passwd('old', 'new')
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Users`` does not implement ``passwd``'
        )

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

        self.checkOutput("""\
        <function ...<lambda> at ...>
        """, str(ugm.roles_storage))

        # Abstract ugm behavior does not implement ``add_role``,
        # ``remove_role``, ``roles`` and ``__call__``
        user = users['someuser'] = UserNode()
        with self.assertRaises(NotImplementedError) as arc:
            ugm.add_role('role', user)
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Ugm`` does not implement ``add_role``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            ugm.remove_role('role', user)
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Ugm`` does not implement ``remove_role``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            ugm.roles(user)
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Ugm`` does not implement ``roles``'
        )

        with self.assertRaises(NotImplementedError) as arc:
            ugm()
        self.assertEqual(
            str(arc.exception),
            'Abstract ``Ugm`` does not implement ``__call__``'
        )
