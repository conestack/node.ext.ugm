import os
import crypt
import hashlib
from odict import odict
from plumber import (
    plumber,
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
    User as UserPart,
    Group as GroupPart,
    Users as UsersPart,
    Groups as GroupsPart,
    Ugm as UgmPart,
)


class FileStorage(Storage):
    """Storage part for key/value pairs.
    
    Cannot contain node children. Useful for node attributes stored in a file.
    """
    
    allow_non_node_childs = extend(True)
    
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
                # XXX: save delimiter escaping
                k, v = line.split(':')
                data[k.decode('utf-8')] = v.strip('\n').decode('utf-8')
    
    @default
    def write_file(self):
        lines = list()
        if hasattr(self, '_storage_data'):
            data = self._storage_data
        else:
            data = dict()
        for k, v in data.items():
            if isinstance(k, unicode):
                k = k.encode('utf-8')
            if isinstance(v, unicode):
                v = v.encode('utf-8')
            line = ':'.join([k, v]) + '\n'
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


def plumbing(*parts):
    return (
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        Nodify,
    ) + parts


class User(object):
    __metaclass__ = plumber
    __plumbing__ = (
        NodeChildValidate,
        Nodespaces,
        Attributes,
        Nodify,
        UserPart,
        DefaultInit,
    )
    
    def user_data_attributes_factory(self, name=None, parent=None):
        user_data_dir = os.path.join(parent.data_directory, 'users')
        if not os.path.exists(user_data_dir):
            os.mkdir(user_data_dir)
        user_data_path = os.path.join(user_data_dir, parent.name)
        return FileAttributes(name, parent, user_data_path)
    
    attributes_factory = user_data_attributes_factory
    
    def __init__(self, name=None, parent=None, data_directory=None):
        self.__name__ = name
        self.__parent__ = parent
        self.data_directory = data_directory
    
    def __setitem__(self, key, value):
        raise NotImplementedError(u"User object cannot contain children.")
    
    @locktree
    def __call__(self):
        self.attrs()
    
    @property
    def groups(self):
        groups = self.parent.parent.groups
        ret = list()
        for group in groups.values():
            if self.name in group.member_ids:
                ret.append(group)
        return ret


class Group(object):
    __metaclass__ = plumber
    __plumbing__ = (
        NodeChildValidate,
        Nodespaces,
        Attributes,
        Nodify,
        GroupPart,
        DefaultInit,
    )
    
    def group_data_attributes_factory(self, name=None, parent=None):
        group_data_dir = os.path.join(parent.data_directory, 'groups')
        if not os.path.exists(group_data_dir):
            os.mkdir(group_data_dir)
        group_data_path = os.path.join(group_data_dir, parent.name)
        return FileAttributes(name, parent, group_data_path)
    
    attributes_factory = group_data_attributes_factory
    
    def __init__(self, name=None, parent=None, data_directory=None):
        self.__name__ = name
        self.__parent__ = parent
        self.data_directory = data_directory
    
    @locktree
    def __setitem__(self, key, value):
        if key != value.name:
            raise RuntimeError(u"Id missmatch at attemp to add group member.")
        if not key in self.member_ids:
            self._add_member(key)
    
    def __getitem__(self, key):
        return self.parent.parent.users[key]
    
    @locktree
    def __delitem__(self, key):
        if not key in self.member_ids:
            raise KeyError(key)
        self._remove_member(key)
    
    def __iter__(self):
        for id in self.member_ids:
            yield id
    
    @locktree
    def __call__(self):
        self.attrs()
    
    @property
    def users(self):
        return [self.parent.parent.users[id] for id in self.member_ids]
    
    @property
    def member_ids(self):
        return [id for id in self.parent.storage[self.name].split(',') if id]
    
    def _add_member(self, id):
        member_ids = self.member_ids
        member_ids.append(id)
        member_ids = sorted(member_ids)
        self.parent.storage[self.name] = ','.join(member_ids)
    
    def _remove_member(self, id):
        member_ids = self.member_ids
        member_ids.remove(id)
        member_ids = sorted(member_ids)
        self.parent.storage[self.name] = ','.join(member_ids)


class Users(object):
    __metaclass__ = plumber
    __plumbing__ = plumbing(UsersPart, FileStorage)
    
    def __init__(self, name=None, parent=None,
                 file_path=None, data_directory=None):
        self.__name__ = name
        self.__parent__ = parent
        self.file_path = file_path
        self.data_directory = data_directory
        self._mem_storage = dict()
    
    def __getitem__(self, key):
        if not key in self.storage:
            raise KeyError(key)
        if key in self._mem_storage:
            return self._mem_storage[key]
        with TreeLock(self):
            self._mem_storage[key] = User(data_directory=self.data_directory)
    
    @locktree
    def __setitem__(self, key, value):
        # set empty password on new added user.
        if not key in self.storage:
            self.storage[key] = ''
        self._mem_storage[key] = value
    
    @locktree
    def __call__(self):
        self.write_file()
        for value in self.values():
            value()
    
    def search(self, **kw):
        ret = list()
        for user in self.values():
            for k, v in kw.items():
                if k == 'id':
                    if user.name == v:
                        ret.append(self._search_result_item(user))
                        continue
                val = user.attrs.get(k)
                if val and val.lower().startswith(v.lower()):
                    ret.append(self._search_result_item(user))
        return ret
    
    def _search_result_item(self, node):
        ret = dict()
        for k, v in node.attrs.items():
            ret[k] = v
        ret['id'] = node.name
        return ret
    
    def create(self, id, **kw):
        user = User(name=id, parent=self, data_directory=self.data_directory)
        for k, v in kw.items():
            user.attrs[k] = v
        self[id] = user
        return user
    
    def authenticate(self, id=None, pw=None):
        if not id in self.storage:
            return False
        # cannot authenticate user with unset password
        if not self.storage[id]:
            return False
        return self._chk_pw(pw, self.storage[id])
    
    def passwd(self, id, oldpw, newpw):
        if not id in self.storage:
            raise ValueError(u"User with id '%s' does not exist." % id)
        # case pwd overwrite
        if self.storage[id]:
            if not self._chk_pw(oldpw, self.storage[id]):
                raise ValueError(u"Old password does not match.")
        self.storage[id] = crypt.crypt(newpw, self._get_salt(newpw))
    
    def _get_salt(self, plain):
        hash = hashlib.md5()
        hash.update(plain)
        return hash.digest()[:2]
    
    def _chk_pw(self, plain, crypted):
        return crypted == crypt.crypt(plain, self._get_salt(plain))


class Groups(object):
    __metaclass__ = plumber
    __plumbing__ = plumbing(GroupsPart, FileStorage)
    
    def __init__(self, name=None, parent=None,
                 file_path=None, data_directory=None):
        self.__name__ = name
        self.__parent__ = parent
        self.file_path = file_path
        self.data_directory = data_directory
        self._mem_storage = dict()
    
    def __getitem__(self, key):
        if not key in self.storage:
            raise KeyError(key)
        if key in self._mem_storage:
            return self._mem_storage[key]
        with TreeLock(self):
            self._mem_storage[key] = Group(data_directory=self.data_directory)
    
    @locktree
    def __setitem__(self, key, value):
        # set empty group members on new added group.
        if not key in self.storage:
            self.storage[key] = ''
        self._mem_storage[key] = value
    
    @locktree
    def __call__(self):
        self.write_file()
        for value in self.values():
            value()
    
    def search(self, **kw):
        ret = list()
        for group in self.values():
            for k, v in kw.items():
                if k == 'id':
                    if group.name == v:
                        ret.append(self._search_result_item(group))
                        continue
                val = group.attrs.get(k)
                if val and val.lower().startswith(v.lower()):
                    ret.append(self._search_result_item(group))
        return ret
    
    def _search_result_item(self, node):
        ret = dict()
        for k, v in node.attrs.items():
            ret[k] = v
        ret['id'] = node.name
        return ret
    
    def create(self, id, **kw):
        group = Group(name=id, parent=self, data_directory=self.data_directory)
        for k, v in kw.items():
            group.attrs[k] = v
        self[id] = group
        return group


class Ugm(object):
    __metaclass__ = plumber
    __plumbing__ = plumbing(UgmPart, DefaultInit, OdictStorage)
    
    def role_attributes_factory(self, name=None, parent=None):
        return FileAttributes(name, parent, parent.roles_file)
    
    attributes_factory = role_attributes_factory
    
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
    
    @property
    def users(self):
        return self['users']
    
    @property
    def groups(self):
        return self['groups']
    
    def __getitem__(self, key):
        if not key in self.storage:
            if key == 'users':
                self['users'] = Users(file_path=self.users_file,
                                      data_directory=self.data_directory)
            else:
                self['groups'] = Groups(file_path=self.groups_file,
                                      data_directory=self.data_directory)
        return self.storage[key]
    
    @locktree
    def __setitem__(self, key, value):
        self._chk_key(key)
        self.storage[key] = value
    
    def __delitem__(self):
        raise NotImplementedError(u"Operation forbidden on this node.")
    
    @locktree
    def __call__(self):
        self.attrs()
        self.users()
        self.groups()
    
    def _chk_key(self, key):
        if not key in ['users', 'groups']:
            raise KeyError(key)