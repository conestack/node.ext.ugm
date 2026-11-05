"""Protect the hashes of the former format in a users file right away.

They would otherwise stay until the next login of each user, which might never
happen. Needs no password and no user has to change it. Run it once while the
application is stopped, which would otherwise write its own copy back. Keep a
backup of the file, an older version of this package cannot read the result::

    python -m node.ext.ugm.wrap_passwords /path/to/users
"""

from node.ext.ugm.file import Users
from node.ext.ugm.password import wrap_legacy_hash
import os
import sys


def main(argv):
    """Wrap the hashes in a users file.

    :param argv: List containing the path of the users file.
    :return: The exit code.
    """
    if len(argv) != 1 or not os.path.isfile(argv[0]):
        print('Usage: python -m node.ext.ugm.wrap_passwords /path/to/users')
        return 2
    users = Users(file_path=argv[0])
    storage = users.storage
    wrapped = 0
    malformed = []
    for user_id, stored in list(storage.items()):
        if not stored:
            continue
        try:
            value = wrap_legacy_hash(stored)
        except ValueError:
            malformed.append(user_id)
            continue
        if value != stored:
            storage[user_id] = value
            wrapped += 1
    users.write_file()
    print(f'{wrapped} of {len(storage)} passwords wrapped.')
    if malformed:
        print(f'Malformed, left as they are: {", ".join(malformed)}')
        return 1
    return 0


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
