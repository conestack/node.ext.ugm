import os
from odict import odict
from plumber import (
    plumber,
    default,
    extend,
    Part,
)
from zope.interface import implements
from node.interfaces import IStorage
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


def crypt_check(password, hashed):
    from crypt import crypt
    salt = hashed[:2]
    return hashed == crypt(password, salt)


def plain_check(password, hashed):
    return hashed == password


class FileStorage(Storage):
    """Storage part for key/value pairs.
    
    Cannot contain node children. Useful for node attributes stored in a file.
    """
    
    file_path = default(None)
    allow_non_node_childs = extend(True)
    
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
    def __call__(self):
        lines = list()
        for k, v in self._storage_data.items():
            line = ':'.join([k.encode('utf-8'), v.encode('utf-8')]) + '\n'
            lines.append(line)
        with open(self.file_path, 'w') as file:
            file.writelines(lines)


def plumbing(*parts):
    return (
        NodeChildValidate,
        Nodespaces,
        Adopt,
        Attributes,
        DefaultInit,
        Nodify,
    ) + parts


class User(object):
    __metaclass__ = plumber
    __plumbing__ = plumbing(UserPart, OdictStorage)


class Group(object):
    __metaclass__ = plumber
    __plumbing__ = plumbing(GroupPart, OdictStorage)


class Users(object):
    __metaclass__ = plumber
    __plumbing__ = plumbing(UsersPart, FileStorage)


class Groups(object):
    __metaclass__ = plumber
    __plumbing__ = plumbing(GroupsPart, FileStorage)


class Ugm(object):
    __metaclass__ = plumber
    __plumbing__ = plumbing(UgmPart, OdictStorage)
    
    def __init__(self, name=None, parent=None,
                 user_file=None, groups_file=None, roles_file=None):
        self.__name__ = name
        self.__parent__ = parent
        self.user_file = user_file
        self.groups_file = groups_file
        self.roles_file = roles_file