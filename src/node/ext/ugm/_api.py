from plumber import (
    Part,
    default,
    extend,
)


class Principal(Part):
    """Turn a node into a principal.
    """
    
    @extend
    @property
    def id(self):
        return self.name

    @extend
    def __iter__(self):
        return iter(list())


class User(Principal):
    """Turn a node into a user.
    """
    
    @extend
    @property
    def login(self):
        return self.attrs.get('login', self.name)

    @extend
    def authenticate(self, pw):
        """Expect an ``authenticate`` function on ``self.parent``.
        """
        return bool(self.parent.authenticate(id=self.id, pw=pw))

    @extend
    def passwd(self, oldpw, newpw):
        """Set password for user. Expect a ``passwd`` function on
        ``self.parent``.
        """
        self.parent.passwd(id=self.id, oldpw=oldpw, newpw=newpw)
    
    @default
    @property
    def groups(self, **kw):
        """List of groups this user is member of.
        """
        raise NotImplementedError(u"Abstract ``User`` does not implement "
                                  u"``groups``")


class Group(Principal):
    """Turn a node into a group.
    """
    
    @default
    @property
    def users(self, **kw):
        """List of users contained in this group.
        """
        raise NotImplementedError(u"Abstract ``Group`` does not implement "
                                  u"``users``")


class Principals(Part):
    """Turn a node into a source of principals.
    
    Supposed to be used in conjunction with a node storage part.
    """
    principal_factory = default(None)

    @extend
    @property
    def ids(self):
        return list(self.__iter__())

    @default
    def search(self, **kw):
        raise NotImplementedError(u"Abstract ``Principals`` does not implement "
                                  u"``search``")


class Users(Principals):
    """Turn a node into source of users.
    """
    
    @default
    def authenticate(self, id=None, pw=None):
        """Authenticate user id with password.
        """
        raise NotImplementedError(u"Abstract ``Users`` does not implement "
                                  u"``authenticate``")
    
    @default
    def passwd(self, id, oldpw, newpw):
        """Set new password for user with id.
        """
        raise NotImplementedError(u"Abstract ``Users`` does not implement "
                                  u"``passwd``")


class Groups(Principals):
    """Turn a node into source of groups.
    """


class Ugm(Part):
    """Turn a node into user and group management API.
    """
    
    # node.ext.ugm.Users implementation
    users = default(None)
    
    # node.ext.ugm.Groups implementation
    groups = default(None)
    
    @default
    def roles(self, principal):
        """Return roles for principal.
        """
        raise NotImplementedError(u"Abstract ``Ugm`` does not implement "
                                  u"``roles``")