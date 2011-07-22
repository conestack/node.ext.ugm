from plumber import (
    Part,
    default,
    extend,
)
from zope.interface import implements
from node.ext.ugm.interfaces import (
    IPrincipal,
    IUser,
    IGroup,
    IPrincipals,
    IUsers,
    IGroups,
    IUgm,
)


class Principal(Part):
    """Turn a node into a principal.
    """
    implements(IPrincipal)
    
    @extend
    @property
    def id(self):
        return self.name

    @extend
    def __iter__(self):
        return iter(list())
    
    @default
    def add_role(self, role):
        raise NotImplementedError(u"Abstract ``Principal`` does not implement "
                                  u"``add_role``")
    
    @default
    def remove_role(self, role):
        raise NotImplementedError(u"Abstract ``Principal`` does not implement "
                                  u"``remove_role``")
    
    @default
    @property
    def roles(self):
        raise NotImplementedError(u"Abstract ``Principal`` does not implement "
                                  u"``roles``")


class User(Principal):
    """Turn a node into a user.
    """
    implements(IUser)
    
    @extend
    @property
    def login(self):
        return self.attrs.get('login', self.name)

    @extend
    def authenticate(self, pw):
        return bool(self.parent.authenticate(id=self.id, pw=pw))

    @extend
    def passwd(self, oldpw, newpw):
        """Expect ``passwd`` function on ``self.parent`` which should implement
        IUsers.
        """
        self.parent.passwd(id=self.id, oldpw=oldpw, newpw=newpw)
    
    @default
    @property
    def groups(self):
        raise NotImplementedError(u"Abstract ``User`` does not implement "
                                  u"``groups``")


class Group(Principal):
    """Turn a node into a group.
    """
    implements(IGroup)
    
    @default
    @property
    def users(self):
        raise NotImplementedError(u"Abstract ``Group`` does not implement "
                                  u"``users``")
    
    @default
    @property
    def member_ids(self):
        raise NotImplementedError(u"Abstract ``Group`` does not implement "
                                  u"``member_ids``")
    
    @default
    def add(self, id):
        raise NotImplementedError(u"Abstract ``Group`` does not implement "
                                  u"``add``")


class Principals(Part):
    """Turn a node into a source of principals.
    """
    implements(IPrincipals)
    
    principal_factory = default(None)

    @extend
    @property
    def ids(self):
        return list(self.__iter__())

    @default
    def search(self, **kw):
        raise NotImplementedError(u"Abstract ``Principals`` does not implement "
                                  u"``search``")
    
    @default
    def create(self, id, **kw):
        raise NotImplementedError(u"Abstract ``Principals`` does not implement "
                                  u"``create``")


class Users(Principals):
    """Turn a node into source of users.
    """
    implements(IUsers)
    
    @default
    def authenticate(self, id=None, pw=None):
        raise NotImplementedError(u"Abstract ``Users`` does not implement "
                                  u"``authenticate``")
    
    @default
    def passwd(self, id, oldpw, newpw):
        raise NotImplementedError(u"Abstract ``Users`` does not implement "
                                  u"``passwd``")


class Groups(Principals):
    """Turn a node into source of groups.
    """
    implements(IGroups)


class Ugm(Part):
    """Turn a node into user and group management API.
    """
    implements(IUgm)
    
    users = default(None)
    
    groups = default(None)
    
    @default
    def add_role(self, role, principal):
        raise NotImplementedError(u"Abstract ``Ugm`` does not implement "
                                  u"``add_role``")
    
    @default
    def remove_role(self, role, principal):
        raise NotImplementedError(u"Abstract ``Ugm`` does not implement "
                                  u"``remove_role``")
    
    @default
    def roles(self, principal):
        raise NotImplementedError(u"Abstract ``Ugm`` does not implement "
                                  u"``roles``")