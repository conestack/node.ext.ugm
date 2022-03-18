from node.interfaces import IInvalidate
from node.interfaces import ILeaf
from node.interfaces import INode
from zope.interface import Attribute


class IPrincipal(INode):
    """Interface describing a principal."""

    id = Attribute(u"Principal ID")

    def add_role(role):
        """Add role for principal.

        :param role: The role name
        """

    def remove_role(role):
        """Remove role for principal.

        :param role: The role name
        """

    roles = Attribute(u"The roles for this principal.")


class IUser(IPrincipal, ILeaf):
    """Interface describing a user."""

    login = Attribute(u"The login name for this user.")

    def authenticate(pw):
        """Authenticate this user.

        :param pw: User password
        """

    def passwd(oldpw, newpw):
        """Set password for this user.

        :param oldpw: Old password. If old password is None, new password is
            always set, otherwise an Exception is raised.
        :param newpw: New password.
        """

    groups = Attribute(u"List of user referring IGroup implementing objects.")

    group_ids = Attribute(u"List of group id's this user is member of")


class IGroup(IPrincipal):
    """Interface describing a group.

    Children of a group are referring IUser implementing objects.
    """

    users = Attribute(u"List of group referring IUser implementing objects.")

    member_ids = Attribute(u"List of member id's contained in this group.")

    def add(id):
        """Add user with id to group. Raise ``KeyError`` if user not exists.

        :param id: User id.
        """

    def __getitem__(key):
        """Return group related ``User`` object. Raise ``KeyError`` if user not
        member of this group.

        :param key: User id.
        """

    def __delitem__(key):
        """Delete membership of user from this group. Raise ``KeyError`` if
        user not member of this group.

        :param key: User id.
        """

    def __iter__():
        """Iterate over ``member_ids``."""


class IPrincipals(INode, IInvalidate):
    """Interface describing a principals container."""

    ids = Attribute(u"List of contained principal ids.")

    def search(criteria=None, attrlist=None,
               exact_match=False, or_search=False):
        """Search for principals.

        :param criteria: Dict like object defining the principal attributes to
            be matched. If no criteria given, all users are returned.
        :param attrlist: If no ``attrlist`` is given a list of ids is returned.
            By defining attrlist the return format will be
            ``[(id, {attr1: value1, attr2: value2, ...}), ...]``. To get this
            format without any attributs, i.e. empty dicts in the tuples,
            specify an empty attrlist.
        :param exact_match: Raise ValueError if not one match, return format is
            a single key or tuple, if attrlist is specified.
        :param or_search: Flag whether criteria should be ORer or ANDed.
            Defaults to False.
        :return: list of ids - if no ``attrlist`` is given else see ``attrlist``
        """

    def create(_id, **kw):
        """Create a principal by id.

        :param _id: Principal id.
        :param kw: Principal attributes.
        """


class IUsers(IPrincipals):
    """Interface describing a users container.

    Child objects must implement IUser.
    """

    def id_for_login(login):
        """Lookup user id for login name.

        :param login: The login name
        """

    def authenticate(id=None, pw=None):
        """Authenticate user with id.

        :param id: User id
        :param pw: User password
        """

    def passwd(id, oldpw, newpw):
        """Set password for user with id.

        :param id: User id
        :param oldpw: Old password. If None, newpassword is always written.
            This is needed for adding new users.
        :param newpw: New password.
        """


class IGroups(IPrincipals):
    """Interface describing a groups container.

    Child objects must implement IGroup.
    """


class IUgm(INode, IInvalidate):
    """Interface describing user and group management API."""

    users = Attribute(u"IUsers implementation")

    groups = Attribute(u"IGroups implementation")

    # XXX: roles storage is implementation specific and should be removed from
    #      here
    roles_storage = Attribute(u"Callable for persisting roles.")

    def add_role(role, principal):
        """Add role for principal.

        :param role: The role name.
        :param principal: IPrincipal implementing object.
        """

    def remove_role(role, principal):
        """Remove role for principal.

        :param role: The role name.
        :param principal: IPrincipal implementing object.
        """

    def roles(principal):
        """Return list of roles for principal.

        :param principal: IPrincipal implementing object.
        """
