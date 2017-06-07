from node.ext.ugm._api import Group
from node.ext.ugm._api import Groups
from node.ext.ugm._api import Principal
from node.ext.ugm._api import Principals
from node.ext.ugm._api import Ugm
from node.ext.ugm._api import User
from node.ext.ugm._api import Users
from node.ext.ugm.file import Ugm as DefaultUgm


def initialize_default_ugm(config, global_config, local_config):
    """Initialize default file based UGM implementation for cone.app
    """
    users_file = local_config.get('node.ext.ugm.users_file')
    groups_file = local_config.get('node.ext.ugm.groups_file')
    roles_file = local_config.get('node.ext.ugm.roles_file')
    datadir = local_config.get('node.ext.ugm.datadir')
    ugm = DefaultUgm(name='ugm',
                     users_file=users_file,
                     groups_file=groups_file,
                     roles_file=roles_file,
                     data_directory=datadir)
    try:
        if local_config.get('cone.auth_impl') == 'node.ext.ugm':
            cone.app.cfg.auth = ugm                           # pragma no cover
    except Exception:                                         # pragma no cover
        pass # case uninstalled cone.app. testing purpose     # pragma no cover
    return ugm


try:
    import cone.app                                            # pragma no cover
    cone.app.register_main_hook(initialize_default_ugm)        # pragma no cover
except ImportError:                                            # pragma no cover
    # cone.app not installed
    pass                                                       # pragma no cover
