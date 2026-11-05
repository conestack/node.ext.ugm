from node.ext.ugm import password
from node.ext.ugm.password import check_password
from node.ext.ugm.password import hash_password
from node.ext.ugm.password import needs_rehash
from node.ext.ugm.password import reject_password
from node.ext.ugm.password import wrap_legacy_hash
from unittest import mock
import base64
import hashlib
import importlib
import os
import unittest


def legacy_hash(value, salt=b'12345678'):
    digest = hashlib.sha256(value.encode('utf-8') + salt).digest()
    return base64.b64encode(digest + salt).decode()


def with_cost(stored, n):
    marker, _cost, *rest = stored.split('$')[1:]
    return '$'.join(['', marker, f'n={n},r=8,p=3', *rest])


class TestHashPassword(unittest.TestCase):
    def test_hash_is_marked_with_format_and_cost(self):
        stored = hash_password('secret')
        self.assertTrue(stored.startswith('$scrypt$n='))
        self.assertIn(',r=8,p=3$', stored)

    def test_hash_is_salted(self):
        self.assertNotEqual(hash_password('secret'), hash_password('secret'))

    def test_check(self):
        stored = hash_password('secret')
        self.assertTrue(check_password('secret', stored))
        self.assertFalse(check_password('wrong', stored))

    def test_check_with_non_ascii_and_bytes(self):
        stored = hash_password('sécret')
        self.assertTrue(check_password('sécret', stored))
        self.assertTrue(check_password('sécret'.encode(), stored))
        stored = hash_password(b'secret')
        self.assertTrue(check_password('secret', stored))

    def test_check_uses_cost_of_stored_value(self):
        stored = password.format_hash(b'secret', {'n': 8, 'r': 8, 'p': 3})
        self.assertIn('n=8,', stored)
        self.assertTrue(check_password('secret', stored))

    def test_value_contains_no_delimiter_of_user_file(self):
        self.assertNotIn(':', hash_password('secret'))
        self.assertNotIn(':', wrap_legacy_hash(legacy_hash('secret')))
        self.assertNotIn('\n', hash_password('secret'))


class TestLegacyHash(unittest.TestCase):
    def test_check(self):
        stored = legacy_hash('secret')
        self.assertTrue(check_password('secret', stored))
        self.assertFalse(check_password('wrong', stored))

    def test_check_with_non_ascii(self):
        self.assertTrue(check_password('sécret', legacy_hash('sécret')))


class TestWrapLegacyHash(unittest.TestCase):
    def test_wrapped_hash_checks_the_password(self):
        wrapped = wrap_legacy_hash(legacy_hash('secret'))
        self.assertTrue(wrapped.startswith('$scrypt-sha256$n='))
        self.assertTrue(check_password('secret', wrapped))
        self.assertFalse(check_password('wrong', wrapped))

    def test_wrapped_hash_does_not_contain_the_former_value(self):
        stored = legacy_hash('secret')
        digest = base64.b64encode(base64.b64decode(stored)[:32]).decode()
        self.assertNotIn(digest, wrap_legacy_hash(stored))

    def test_hashes_of_the_current_format_stay_as_they_are(self):
        stored = hash_password('secret')
        self.assertEqual(wrap_legacy_hash(stored), stored)
        wrapped = wrap_legacy_hash(legacy_hash('secret'))
        self.assertEqual(wrap_legacy_hash(wrapped), wrapped)

    def test_malformed_value_raises(self):
        for value in ('not base64!', base64.b64encode(b'too short').decode()):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    wrap_legacy_hash(value)


class TestNeedsRehash(unittest.TestCase):
    def test_former_formats(self):
        self.assertTrue(needs_rehash(legacy_hash('secret')))
        self.assertTrue(needs_rehash(wrap_legacy_hash(legacy_hash('secret'))))

    def test_current_format(self):
        self.assertFalse(needs_rehash(hash_password('secret')))

    def test_lower_cost(self):
        current = password.COST['n']
        stored = with_cost(hash_password('secret'), current // 2)
        self.assertTrue(needs_rehash(stored))

    def test_higher_cost_is_never_lowered(self):
        current = password.COST['n']
        stored = with_cost(hash_password('secret'), current * 2)
        self.assertFalse(needs_rehash(stored))


class TestMalformedValues(unittest.TestCase):
    def test_check_fails_closed(self):
        salt = base64.b64encode(b'a' * 16).decode()
        for value in (
            '',
            None,
            'not base64!',
            base64.b64encode(b'too short').decode(),
            '$unknown$a$b',
            '$scrypt$',
            '$scrypt$x$y$z',
            f'$scrypt$n=16,r=8,p=3${salt}',
            f'$scrypt$n=16,r=8,p=3${salt}$!!',
            f'$scrypt$n=15,r=8,p=3${salt}${salt}',
            '$scrypt-sha256$n=16,r=8,p=3$a',
        ):
            with self.subTest(value=value):
                self.assertFalse(check_password('secret', value))


class TestRejectPassword(unittest.TestCase):
    def test_spends_the_time_of_a_check_and_denies(self):
        with mock.patch.object(password, 'hashlib', wraps=hashlib) as patched:
            self.assertFalse(reject_password('secret'))
            self.assertFalse(reject_password(b'secret'))
        self.assertEqual(patched.scrypt.call_count, 2)
        self.assertEqual(patched.scrypt.call_args.kwargs['n'], password.COST['n'])


class TestCost(unittest.TestCase):
    def tearDown(self):
        importlib.reload(password)

    def test_test_runs_use_a_cheap_cost(self):
        with mock.patch.dict(os.environ, {'TESTRUN_MARKER': '1'}):
            importlib.reload(password)
        self.assertEqual(password.COST, {'n': 2**4, 'r': 8, 'p': 3})

    def test_cost_outside_test_runs(self):
        environ = {k: v for k, v in os.environ.items() if k != 'TESTRUN_MARKER'}
        with mock.patch.dict(os.environ, environ, clear=True):
            importlib.reload(password)
        self.assertEqual(password.COST, {'n': 2**15, 'r': 8, 'p': 3})

    def test_production_cost_is_accepted_by_scrypt(self):
        stored = password.format_hash(b'secret', {'n': 2**15, 'r': 8, 'p': 3})
        self.assertTrue(check_password('secret', stored))
