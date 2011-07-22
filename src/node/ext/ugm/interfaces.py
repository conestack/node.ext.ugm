from zope.interface import Attribute
from node.interfaces import (
    INode,
    ILeaf,
)


class IPrincipal(INode):
    """Interface describing a principal.
    """
    
    id = Attribute(u"Principal ID")
    
    def add_role(role):
        """Add role for principal.
        
        role
            The role name
        """
        
    
    def remove_role(role):
        """Remove role for principal.
        
        role
            The role name
        """
    
    roles = Attribute(u"The roles for this principal.")


class IUser(IPrincipal, ILeaf):
    """Interface describing a user.
    """
    
    login = Attribute(u"The login name for this user.")
    
    def authenticate(pw):
        """Authenticate this user.
        
        pw
            User password
        """

    def passwd(oldpw, newpw):
        """Set password for this user.
        
        oldpw
            Old password. If None, newpassword is always written. This
            is needed for adding new users.
        
        newpw
            New password.
        """
    
    groups = Attribute("List of user referring IGroup implementing objects.")


class IGroup(IPrincipal):
    """Interface describing a group.
    
    Children of a group are referring IUser implementing objects.
    """
    
    users = Attribute(u"List of group referring IUser implementing objects.")
    
    member_ids = Attribute(u"List of member ids contained in this group.")
    
    def add(id):
        """Add user with id to group.
        
        id
            User id.
        """


class IPrincipals(INode):
    """Interface describing a principals container.
    """
    
    ids = Attribute(u"List of contained principal ids.")

    def search(**kw):
        """Search for principals.
        
        kw
            Search criteria.
        
        XXX: more concrete search criteria, as long as they are abstract
             enough.
        """
    
    def create(_id, **kw):
        """Create a principal by id.
        
        _id
            Principal id.
        
        kw
            Principal attributes.
        """


class IUsers(IPrincipals):
    """Interface describing a users container.
    
    Child objects must implement IUser.
    """
    
    def authenticate(id=None, pw=None):
        """Authenticate user with id.
        
        id
            User id
        
        pw
            User password
        """
    
    def passwd(id, oldpw, newpw):
        """Set password for user with id.
        
        id
            User id
        
        oldpw
            Old password. If None, newpassword is always written. This
            is needed for adding new users.
        
        newpw
            New password.
        """


class IGroups(IPrincipals):
    """Interface describing a groups container.
    
    Child objects must implement IGroup.
    """


class IUgm(INode):
    """Interface describing user and group management API.
    """
    
    users = Attribute(u"IUsers implementation")
    
    groups = Attribute(u"IGroups implementation")
    
    def add_role(role, principal):
        """Add role for principal.
        
        role
            The role name.
        
        principal
            IPrincipal implementing object.
        """
    
    def remove_role(role, principal):
        """Remove role for principal.
        
        role
            The role name.
        
        principal
            IPrincipal implementing object.
        """
    
    def roles(principal):
        """Return list of roles for principal.
        
        principal
            IPrincipal implementing object.
        """