"""Hashing of user passwords, shared by the UGM backends.

Stored values have one of these formats:

``$scrypt$n=32768,r=8,p=3$<salt>$<hash>``
    The password hashed with scrypt.

``$scrypt-sha256$n=32768,r=8,p=3$<salt>$<former salt>$<hash>``
    A hash of the former format hashed once more with scrypt. Created without
    knowing the password, see ``wrap_legacy_hash``. Replaced by the first format
    with the next successful login.

``<base64 of sha256(password + salt) + salt>``
    The former format, it has no marker. Replaced the same way.
"""

import base64
import hashlib
import hmac
import os
import re


SCRYPT = '$scrypt$'
WRAPPED = '$scrypt-sha256$'
# ``r`` and ``p`` trade memory against time, these need 32 MiB per check. Test
# runs hash thousands of passwords, there the cost would only slow them down. A
# stored hash never gets replaced by a cheaper one, see ``needs_rehash``.
COST = {
    'n': 2**4 if os.environ.get('TESTRUN_MARKER') else 2**15,
    'r': 8,
    'p': 3,
}
SALT_LENGTH = 16
DIGEST_LENGTH = 32
LEGACY_SALT_LENGTH = 8
COST_FORMAT = re.compile(r'n=(\d+),r=(\d+),p=(\d+)')


def _encoded(password):
    return password.encode('utf-8') if isinstance(password, str) else password


def _base64(value):
    return base64.b64encode(value).decode()


def _scrypt(data, salt, cost):
    # The default of ``maxmem`` is too small for higher costs.
    maxmem = 2 * 128 * cost['n'] * cost['r']
    return hashlib.scrypt(
        data,
        salt=salt,
        n=cost['n'],
        r=cost['r'],
        p=cost['p'],
        maxmem=maxmem,
        dklen=DIGEST_LENGTH,
    )


def _format_cost(cost):
    return f'n={cost["n"]},r={cost["r"]},p={cost["p"]}'


def _parse_cost(value):
    match = COST_FORMAT.fullmatch(value)
    if not match:
        raise ValueError('Malformed cost')
    n, r, p = (int(part) for part in match.groups())
    return {'n': n, 'r': r, 'p': p}


def _parse(stored, marker):
    """Split a stored value of the marked formats into cost and binary fields."""
    cost, *fields = stored[len(marker) :].split('$')
    return _parse_cost(cost), [base64.b64decode(field, validate=True) for field in fields]


def _parse_legacy(stored):
    raw = base64.b64decode(stored, validate=True)
    if len(raw) != DIGEST_LENGTH + LEGACY_SALT_LENGTH:
        raise ValueError('Malformed hash')
    return raw[:DIGEST_LENGTH], raw[DIGEST_LENGTH:]


def _sha256(password, salt):
    return hashlib.sha256(password + salt).digest()


def _verify(password, stored):
    if stored.startswith(SCRYPT):
        cost, (salt, digest) = _parse(stored, SCRYPT)
        return hmac.compare_digest(_scrypt(password, salt, cost), digest)
    if stored.startswith(WRAPPED):
        cost, (salt, legacy_salt, digest) = _parse(stored, WRAPPED)
        legacy_digest = _sha256(password, legacy_salt)
        return hmac.compare_digest(_scrypt(legacy_digest, salt, cost), digest)
    digest, salt = _parse_legacy(stored)
    return hmac.compare_digest(_sha256(password, salt), digest)


def format_hash(password, cost):
    """Hash a password with given cost.

    :param password: The password as bytes.
    :param cost: Dict containing the scrypt parameters ``n``, ``r`` and ``p``.
    :return: The value to store.
    """
    salt = os.urandom(SALT_LENGTH)
    digest = _scrypt(password, salt, cost)
    return f'{SCRYPT}{_format_cost(cost)}${_base64(salt)}${_base64(digest)}'


def hash_password(password):
    """Hash a password.

    :param password: The password as string or bytes.
    :return: The value to store.
    """
    return format_hash(_encoded(password), COST)


def check_password(password, stored):
    """Check a password against a stored value of any format.

    :param password: The password as string or bytes.
    :param stored: The stored value, ``None`` if the user has no password.
    :return: Whether the password matches. Empty and malformed values never match.
    """
    if not stored:
        return False
    try:
        return _verify(_encoded(password), stored)
    except ValueError:
        return False


def needs_rehash(stored):
    """Check whether a stored value should be replaced after a successful login.

    :param stored: The stored value, which already matched the password.
    :return: Whether it has a former format or a lower cost than the current one.
    """
    if not stored.startswith(SCRYPT):
        return True
    cost, _fields = _parse(stored, SCRYPT)
    return any(cost[name] < COST[name] for name in COST)


def wrap_legacy_hash(stored):
    """Protect a hash of the former format without knowing the password.

    :param stored: The stored value.
    :return: The value to store. Values of the other formats stay as they are.
    :raises ValueError: If the value is malformed.
    """
    if stored.startswith((SCRYPT, WRAPPED)):
        return stored
    digest, legacy_salt = _parse_legacy(stored)
    salt = os.urandom(SALT_LENGTH)
    wrapped = _scrypt(digest, salt, COST)
    fields = (_base64(salt), _base64(legacy_salt), _base64(wrapped))
    return f'{WRAPPED}{_format_cost(COST)}${"$".join(fields)}'


def reject_password(password):
    """Deny a login in the time a check takes.

    Otherwise the answer time tells whether a user exists.

    :param password: The password as string or bytes.
    :return: Always ``False``.
    """
    _scrypt(_encoded(password), bytes(SALT_LENGTH), COST)
    return False
