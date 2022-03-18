from node.ext.ugm.interfaces import IGroup
from node.ext.ugm.interfaces import IGroups
from node.ext.ugm.interfaces import IPrincipal
from node.ext.ugm.interfaces import IPrincipals
from node.ext.ugm.interfaces import IUgm
from node.ext.ugm.interfaces import IUser
from node.ext.ugm.interfaces import IUsers
from plumber import Behavior
from plumber import default
from plumber import finalize
from plumber import override
from zope.interface import implementer


@implementer(IPrincipal)
class Principal(Behavior):
    """Turn a node into a principal."""

    @override
    @property
    def id(self):
        return self.name

    @default
    def add_role(self, role):
        raise NotImplementedError(
            'Abstract ``Principal`` does not implement ``add_role``'
        )

    @default
    def remove_role(self, role):
        raise NotImplementedError(
            'Abstract ``Principal`` does not implement ``remove_role``'
        )

    @default
    @property
    def roles(self):
        raise NotImplementedError(
            'Abstract ``Principal`` does not implement ``roles``'
        )

    @default
    def __call__(self):
        raise NotImplementedError(
            'Abstract ``Principal`` does not implement ``__call__``'
        )


@implementer(IUser)
class User(Principal):
    """Turn a node into a user."""

    @finalize
    def __getitem__(self, key):
        # __getitem__ API not supported
        raise NotImplementedError('User does not support ``__getitem__``')

    @finalize
    def __setitem__(self, key, value):
        # __setitem__ API not supported
        raise NotImplementedError('User does not support ``__setitem__``')

    @finalize
    def __delitem__(self, key):
        # __delitem__ API not supported
        raise NotImplementedError('User does not support ``__delitem__``')

    @finalize
    def __iter__(self):
        # __iter__ API not supported
        return iter([])

    @override
    @property
    def login(self):
        return self.attrs.get('login', self.name)

    @override
    def authenticate(self, pw):
        return bool(self.parent.authenticate(id=self.id, pw=pw))

    @override
    def passwd(self, oldpw, newpw):
        """Expect ``passwd`` function on ``self.parent`` which should implement
        IUsers.
        """
        self.parent.passwd(id=self.id, oldpw=oldpw, newpw=newpw)

    @default
    @property
    def groups(self):
        raise NotImplementedError(
            'Abstract ``User`` does not implement ``groups``'
        )

    @default
    @property
    def group_ids(self):
        raise NotImplementedError(
            'Abstract ``User`` does not implement ``group_ids``'
        )


@implementer(IGroup)
class Group(Principal):
    """Turn a node into a group."""

    @finalize
    def __setitem__(self, key, value):
        # __setitem__ API not supported
        raise NotImplementedError('Group does not support ``__setitem__``')

    @default
    def __getitem__(self, key):
        raise NotImplementedError(
            'Abstract ``Group`` does not implement ``__getitem__``'
        )

    @default
    def __delitem__(self, key):
        raise NotImplementedError(
            'Abstract ``Group`` does not implement ``__delitem__``'
        )

    @default
    def __iter__(self):
        raise NotImplementedError(
            'Abstract ``Group`` does not implement ``__iter__``'
        )

    @default
    @property
    def users(self):
        raise NotImplementedError(
            'Abstract ``Group`` does not implement ``users``'
        )

    @default
    @property
    def member_ids(self):
        raise NotImplementedError(
            'Abstract ``Group`` does not implement ``member_ids``'
        )

    @default
    def add(self, id):
        raise NotImplementedError(
            'Abstract ``Group`` does not implement ``add``'
        )


@implementer(IPrincipals)
class Principals(Behavior):
    """Turn a node into a source of principals."""

    principal_factory = default(None)

    @override
    @property
    def ids(self):
        return list(self.__iter__())

    @default
    def search(self, **kw):
        raise NotImplementedError(
            'Abstract ``Principals`` does not implement ``search``'
        )

    @default
    def create(self, _id, **kw):
        raise NotImplementedError(
            'Abstract ``Principals`` does not implement ``create``'
        )

    @default
    def __call__(self):
        raise NotImplementedError(
            'Abstract ``Principals`` does not implement ``__call__``'
        )

    @default
    def invalidate(self, key=None):
        raise NotImplementedError(
            'Abstract ``Principals`` does not implement ``invalidate``'
        )


@implementer(IUsers)
class Users(Principals):
    """Turn a node into source of users."""

    @default
    def id_for_login(self, login):
        raise NotImplementedError(
            'Abstract ``Users`` does not implement ``id_for_login``'
        )

    @default
    def authenticate(self, id=None, pw=None):
        raise NotImplementedError(
            'Abstract ``Users`` does not implement ``authenticate``'
        )

    @default
    def passwd(self, id, oldpw, newpw):
        raise NotImplementedError(
            'Abstract ``Users`` does not implement ``passwd``'
        )


@implementer(IGroups)
class Groups(Principals):
    """Turn a node into source of groups."""


@implementer(IUgm)
class Ugm(Behavior):
    """Turn a node into user and group management API."""

    users = default(None)
    groups = default(None)
    roles_storage = default(None)

    @default
    def __call__(self):
        raise NotImplementedError(
            'Abstract ``Ugm`` does not implement ``__call__``'
        )

    @default
    def add_role(self, role, principal):
        raise NotImplementedError(
            'Abstract ``Ugm`` does not implement ``add_role``'
        )

    @default
    def remove_role(self, role, principal):
        raise NotImplementedError(
            'Abstract ``Ugm`` does not implement ``remove_role``'
        )

    @default
    def roles(self, principal):
        raise NotImplementedError(
            'Abstract ``Ugm`` does not implement ``roles``'
        )
