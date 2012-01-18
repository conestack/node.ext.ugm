import os
import crypt
import hashlib
from odict import odict
from plumber import (
    plumber,
    plumb,
    default,
    extend,
    Part,
)
from zope.interface import implements
from node.interfaces import IStorage
from node.locking import (
    locktree,
    TreeLock,
)
from node.parts import (
    NodeChildValidate,
    Nodespaces,
    Adopt,
    Attributes,
    DefaultInit,
    Nodify,
    Storage,
    OdictStorage,
)
from node.ext.ugm import (
    User as BaseUserPart,
    Group as BaseGroupPart,
    Users as BaseUsersPart,
    Groups as BaseGroupsPart,
    Ugm as BaseUgmPart,
)


class FileStorage(Storage):
    """Storage part handling key/value pairs in a file.
    
    Cannot contain node children. Useful for node attributes stored in a file.
    
    XXX: extend node.parts.common.NodeChildValidate by ``allow_node_childs``
         attribute.
    """
    
    allow_non_node_childs = extend(True)
    unicode_keys = default(True)
    unicode_values = default(True)
    delimiter = default(':')
    
    @extend
    def __init__(self, name=None, parent=None, file_path=None):
        self.__name__ = name
        self.__parent__ = parent
        self.file_path = file_path
    
    @default
    @property
    def storage(self):
        if not hasattr(self, '_storage_data'):
            self._storage_data = odict()
            if self.file_path and os.path.isfile(self.file_path):
                self.read_file()
        return self._storage_data
    
    @default
    def read_file(self):
        data = self._storage_data
        with open(self.file_path) as file:
            for line in file:
                k, v = line.split(self.delimiter)
                if not isinstance(k, unicode) and self.unicode_keys:
                    k = k.decode('utf-8')
                if not isinstance(v, unicode) and self.unicode_values:
                    v = v.decode('utf-8')
                data[k] = v.strip('\n')
    
    @default
    def write_file(self):
        lines = list()
        if hasattr(self, '_storage_data'):
            data = self._storage_data
        else:
            data = dict()
        for k, v in data.items():
            if isinstance(k, unicode) and self.unicode_keys:
                k = k.encode('utf-8')
            if isinstance(v, unicode) and self.unicode_values:
                v = v.encode('utf-8')
            line = self.delimiter.join([k, v]) + '\n'
            lines.append(line)
        with open(self.file_path, 'w') as file:
            file.writelines(lines)
    
    @default
    def __call__(self):
        self.write_file()


class FileAttributes(object):
    __metaclass__ = plumber
    __plumbing__ = (
        NodeChildValidate,
        Adopt,
        Nodify,
        FileStorage,
    )


class UserPart(BaseUserPart):
    
    @default
    def user_data_attributes_factory(self, name=None, parent=None):
        user_data_dir = os.path.join(parent.data_directory, 'users')
        if not os.path.exists(user_data_dir):
            os.mkdir(user_data_dir)
        user_data_path = os.path.join(user_data_dir, parent.name)
        return FileAttributes(name, parent, user_data_path)
    
    attributes_factory = default(user_data_attributes_factory)
    
    @extend
    def __init__(self, name=None, parent=None, data_directory=None):
        self.__name__ = name
        self.__parent__ = parent
        self.data_directory = data_directory
    
    @default
    @locktree
    def __call__(self, from_parent=False):
        self.attrs()
        if not from_parent:
            self.parent.parent.attrs()
    
    @default
    def add_role(self, role):
        self.parent.parent.add_role(role, self)
    
    @default
    def remove_role(self, role):
        self.parent.parent.remove_role(role, self)
    
    @default
    @property
    def roles(self):
        return self.parent.parent.roles(self)
    
    @default
    @property
    def groups(self):
        groups = self.parent.parent.groups
        ret = list()
        for group in groups.values():
            if self.name in group.member_ids:
                ret.append(group)
        return ret


class User(object):
    __metaclass__ = plumber
    __plumbing__ = (
        UserPart,
        NodeChildValidate,
        Nodespaces,
        Attributes,
        Nodify,
    )


class GroupPart(BaseGroupPart):
    
    @default
    def group_data_attributes_factory(self, name=None, parent=None):
        group_data_dir = os.path.join(parent.data_directory, 'groups')
        if not os.path.exists(group_data_dir):
            os.mkdir(group_data_dir)
        group_data_path = os.path.join(group_data_dir, parent.name)
        return FileAttributes(name, parent, group_data_path)
    
    attributes_factory = default(group_data_attributes_factory)
    
    @extend
    def __init__(self, name=None, parent=None, data_directory=None):
        self.__name__ = name
        self.__parent__ = parent
        self.data_directory = data_directory
    
    @default
    def __getitem__(self, key):
        return self.parent.parent.users[key]
    
    @default
    @locktree
    def __delitem__(self, key):
        if not key in self.member_ids:
            raise KeyError(key)
        self._remove_member(key)
    
    @default
    def __iter__(self):
        for id in self.member_ids:
            yield id
    
    @default
    @locktree
    def __call__(self, from_parent=False):
        self.attrs()
        if not from_parent:
            self.parent.parent.attrs()
    
    @default
    def add(self, id):
        if not id in self.member_ids:
            self._add_member(id)
    
    @default
    def add_role(self, role):
        self.parent.parent.add_role(role, self)
    
    @default
    def remove_role(self, role):
        self.parent.parent.remove_role(role, self)
    
    @default
    @property
    def roles(self):
        return self.parent.parent.roles(self)
    
    @default
    @property
    def users(self):
        return [self.parent.parent.users[id] for id in self.member_ids]
    
    @default
    @property
    def member_ids(self):
        return [id for id in self.parent.storage[self.name].split(',') if id]
    
    @default
    def _add_member(self, id):
        member_ids = self.member_ids
        member_ids.append(id)
        member_ids = sorted(member_ids)
        self.parent.storage[self.name] = ','.join(member_ids)
    
    @default
    def _remove_member(self, id):
        member_ids = self.member_ids
        member_ids.remove(id)
        member_ids = sorted(member_ids)
        self.parent.storage[self.name] = ','.join(member_ids)


class Group(object):
    __metaclass__ = plumber
    __plumbing__ = (
        GroupPart,
        NodeChildValidate,
        Nodespaces,
        Attributes,
        Nodify,
    )


class SearchPart(Part):
    
    @default
    def _compare_value(self, term, value):
        # XXX: this should be done by regular expressions.
        if term == '*':
            return True
        if not len(term.strip('*')):
            return False
        if term[0] == '*' and term[-1] == '*':
            term = term[1:-1]
            if value.find(term) > -1:
                return True
        if term[0] == '*':
            term = term[1:]
            if value.endswith(term):
                return True
        if term[-1] == '*':
            term = term[:-1]
            if value.startswith(term):
                return True
        if term == value:
            return True
        return False
    
    @default
    def search(self, criteria=None, attrlist=None,
               exact_match=False, or_search=False):
        """This is very slow and primary supposed to be used for testing or
        setups with just a few users and groups.
        """
        found = set()
        if criteria is None:
            return list()
        for principal in self.values():
            # exact match too many
            if exact_match and len(found) > 1:
                raise ValueError(
                    u"Exact match asked but result not unique")
            # or search
            if or_search:
                for key, term in criteria.items():
                    if key == 'id':
                        if self._compare_value(term, principal.name):
                            found.add(principal)
                        continue
                    value = principal.attrs.get(key)
                    if value:
                        if self._compare_value(term, value):
                            found.add(principal)
                            continue
            # and search
            else:
                matches = True
                for key, term in criteria.items():
                    if key == 'id':
                        if not self._compare_value(term, principal.name):
                            matches = False
                            break
                        continue
                    value = principal.attrs.get(key)
                    if not value or not self._compare_value(term, value):
                        matches = False
                        break
                if matches:
                    found.add(principal)
        # exact match zero found
        if exact_match and len(found) == 0:
            raise ValueError(u"Exact match asked but result length is zero")
        # attr list
        if attrlist:
            ret = list()
            for principal in found:
                pdata = dict()
                for key in attrlist:
                    if key == 'id':
                        pdata[key] = principal.name
                        continue
                    pdata[key] = principal.attrs.get(key, '')
                ret.append((principal.name, pdata))
        # keys only
        else:
            ret = [principal.name for principal in found]
        return ret


class UsersPart(SearchPart, BaseUsersPart):
    
    unicode_values = default(False)
    
    @extend
    def __init__(self, name=None, parent=None,
                 file_path=None, data_directory=None):
        self.__name__ = name
        self.__parent__ = parent
        self.file_path = file_path
        self.data_directory = data_directory
        self._mem_storage = dict()
    
    @extend
    def __getitem__(self, key):
        if not key in self.storage:
            raise KeyError(key)
        if key in self._mem_storage:
            return self._mem_storage[key]
        with TreeLock(self):
            user = User(
                name=key, parent=self, data_directory=self.data_directory)
            self._mem_storage[key] = user
            return user
    
    @extend
    @locktree
    def __setitem__(self, key, value):
        # set empty password on new added user.
        if not key in self.storage:
            self.storage[key] = ''
        self._mem_storage[key] = value
    
    @extend
    @locktree
    def __delitem__(self, key):
        user = self[key]
        for group in user.groups:
            del group[user.name]
        del self.storage[key]
        del self._mem_storage[key]
        if key in self.parent.attrs:
            del self.parent.attrs[key]
    
    @extend
    @locktree
    def __call__(self, from_parent=False):
        self.write_file()
        for value in self.values():
            value(True)
        if not from_parent:
            self.parent.attrs()
    
    @default
    def create(self, id, **kw):
        user = User(name=id, parent=self, data_directory=self.data_directory)
        for k, v in kw.items():
            user.attrs[k] = v
        self[id] = user
        return user
    
    @default
    def id_for_login(self, login):
        # XXX
        return login
    
    @default
    def authenticate(self, id=None, pw=None):
        if not id in self.storage:
            return False
        # cannot authenticate user with unset password
        if not self.storage[id]:
            return False
        return self._chk_pw(pw, self.storage[id])
    
    @default
    def passwd(self, id, oldpw, newpw):
        if not id in self.storage:
            raise ValueError(u"User with id '%s' does not exist." % id)
        # case pwd overwrite
        if self.storage[id]:
            if not self._chk_pw(oldpw, self.storage[id]):
                raise ValueError(u"Old password does not match.")
        self.storage[id] = crypt.crypt(newpw, self._get_salt(id))
    
    @default
    def _get_salt(self, id):
        hash = hashlib.md5()
        hash.update(id)
        return hash.digest()[:2]
    
    @default
    def _chk_pw(self, plain, hashed):
        salt = hashed[:2]
        return hashed == crypt.crypt(plain, salt)


class Users(object):
    __metaclass__ = plumber
    __plumbing__ = (
        UsersPart,
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        Nodify,
        FileStorage,
    )


class GroupsPart(SearchPart, BaseGroupsPart):
    
    @extend
    def __init__(self, name=None, parent=None,
                 file_path=None, data_directory=None):
        self.__name__ = name
        self.__parent__ = parent
        self.file_path = file_path
        self.data_directory = data_directory
        self._mem_storage = dict()
    
    @extend
    def __getitem__(self, key):
        if not key in self.storage:
            raise KeyError(key)
        if key in self._mem_storage:
            return self._mem_storage[key]
        with TreeLock(self):
            group = Group(
                name=key, parent=self, data_directory=self.data_directory)
            self._mem_storage[key] = group
            return group
    
    @extend
    @locktree
    def __setitem__(self, key, value):
        # set empty group members on new added group.
        if not key in self.storage:
            self.storage[key] = ''
        self._mem_storage[key] = value
    
    @extend
    @locktree
    def __delitem__(self, key):
        del self.storage[key]
        if key in self._mem_storage:
            del self._mem_storage[key]
        id = 'group:%s' % key
        if id in self.parent.attrs:
            del self.parent.attrs[id]
    
    @extend
    @locktree
    def __call__(self, from_parent=False):
        self.write_file()
        for value in self.values():
            value(True)
        if not from_parent:
            self.parent.attrs()
    
    @default
    def create(self, id, **kw):
        group = Group(name=id, parent=self, data_directory=self.data_directory)
        for k, v in kw.items():
            group.attrs[k] = v
        self[id] = group
        return group


class Groups(object):
    __metaclass__ = plumber
    __plumbing__ = (
        GroupsPart,
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        Nodify,
        FileStorage,
    )


class UgmPart(BaseUgmPart):
    
    @default
    def role_attributes_factory(self, name=None, parent=None):
        attrs = FileAttributes(name, parent, parent.roles_file)
        attrs.delimiter = '::'
        return attrs
    
    attributes_factory = default(role_attributes_factory)
    
    @extend
    def __init__(self,
                 name=None,
                 parent=None,
                 users_file=None,
                 groups_file=None,
                 roles_file=None,
                 data_directory=None):
        self.__name__ = name
        self.__parent__ = parent
        self.users_file = users_file
        self.groups_file = groups_file
        self.roles_file = roles_file
        self.data_directory = data_directory
    
    @extend
    def __getitem__(self, key):
        if not key in self.storage:
            if key == 'users':
                self['users'] = Users(file_path=self.users_file,
                                      data_directory=self.data_directory)
            else:
                self['groups'] = Groups(file_path=self.groups_file,
                                      data_directory=self.data_directory)
        return self.storage[key]
    
    @extend
    @locktree
    def __setitem__(self, key, value):
        self._chk_key(key)
        self.storage[key] = value
    
    @extend
    def __delitem__(self, key):
        raise NotImplementedError(u"Operation forbidden on this node.")
    
    @extend
    def __iter__(self):
        for key in ['users', 'groups']:
            yield key
    
    @extend
    @locktree
    def __call__(self):
        self.attrs()
        self.users(True)
        self.groups(True)
    
    @default
    @property
    def users(self):
        return self['users']
    
    @default
    @property
    def groups(self):
        return self['groups']
    
    @default
    def roles(self, principal):
        id = self._principal_id(principal)
        return self._roles(id)
    
    @default
    @property
    def roles_storage(self):
        return self.attrs
    
    @default
    @locktree
    def add_role(self, role, principal):
        roles = self.roles(principal)
        if role in roles:
            raise ValueError(u"Principal already has role '%s'" % role)
        roles.append(role)
        roles = sorted(roles)
        self.attrs[self._principal_id(principal)] = ','.join(roles)
    
    @default
    @locktree
    def remove_role(self, role, principal):
        roles = self.roles(principal)
        if not role in roles:
            raise ValueError(u"Principal does not has role '%s'" % role)
        roles.remove(role)
        roles = sorted(roles)
        self.attrs[self._principal_id(principal)] = ','.join(roles)
    
    @default
    def _principal_id(self, principal):
        id = principal.name
        if isinstance(principal, Group):
            id = 'group:%s' % id
        return id
    
    @default
    def _roles(self, id):
        attrs = self.attrs
        if not id in attrs:
            return list()
        return [role for role in attrs[id].split(',') if role]
    
    @default
    def _chk_key(self, key):
        if not key in ['users', 'groups']:
            raise KeyError(key)


class Ugm(object):
    __metaclass__ = plumber
    __plumbing__ = (
        UgmPart,
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        DefaultInit,
        Nodify,
        OdictStorage,
    )