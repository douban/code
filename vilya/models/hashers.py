# coding=utf-8
import string
import random
import binascii
import hashlib
import importlib
from collections import OrderedDict


UNUSABLE_PASSWORD_PREFIX = '!'


def gen_random_password(length=20):
    return ''.join(random.choice(string.ascii_letters + string.digits)
                   for i in range(10))


def constant_time_compare(val1, val2):
    if len(val1) != len(val2):
        return False
    result = 0
    for x, y in zip(val1, val2):
        result |= ord(x) ^ ord(y)
    return result == 0


def check_password(password, encoded, preferred='default'):
    preferred = get_hasher(preferred)
    hasher = identify_hasher(encoded)

    is_correct = hasher.verify(password, encoded)
    return is_correct


def make_password(password, salt=None, hasher='default', suffix_length=20):
    if password is None:
        return UNUSABLE_PASSWORD_PREFIX + gen_random_password(suffix_length)
    hasher = get_hasher(hasher)

    if not salt:
        salt = hasher.salt()

    return hasher.encode(password, salt)


def get_hashers():
    return [
        BCryptSHA256PasswordHasher, BCryptPasswordHasher
    ]


def get_hasher(algorithm='default'):
    if hasattr(algorithm, 'algorithm'):
        return algorithm

    elif algorithm == 'default':
        return get_hashers()[0]

    else:
        hasher = next((hasher for hasher in get_hashers()
                       if hasher.algorithm == algorithm), None)
        if hasher is None:
            raise ValueError(
                "Unknown password hashing algorithm '{}'. ".format(algorithm))
        return hasher()


def identify_hasher(encoded):
    algorithm = encoded.split('$', 1)[0]
    return get_hasher(algorithm)


def mask_hash(hash, show=6, char="*"):
    masked = hash[:show]
    masked += char * len(hash[show:])
    return masked


class BasePasswordHasher(object):
    algorithm = None
    library = None

    def _load_library(self):
        if self.library is not None:
            if isinstance(self.library, (tuple, list)):
                name, mod_path = self.library
            else:
                mod_path = self.library
            try:
                module = importlib.import_module(mod_path)
            except ImportError as e:
                raise ValueError("Couldn't load %r algorithm library: %s" %
                                 (self.__class__.__name__, e))
            return module
        raise ValueError("Hasher %r doesn't specify a library attribute" %
                         self.__class__.__name__)

    def salt(self):
        """Generates a cryptographically secure nonce salt in ASCII"""
        return gen_random_password()

    def verify(self, password, encoded):
        raise NotImplementedError(
            'subclasses of BasePasswordHasher must provide a verify() method')

    def encode(self, password, salt):
        """Creates an encoded database value

        The result is normally formatted as "algorithm$salt$hash" and
        must be fewer than 128 characters.
        """
        raise NotImplementedError(
            'subclasses of BasePasswordHasher must provide an encode() method')

    def safe_summary(self, encoded):
        """Returns a summary of safe values

        The result is a dictionary and will be used where the password field
        must be displayed to construct a safe representation of the password.
        """
        raise NotImplementedError(
            'subclasses of BasePasswordHasher must provide a safe_summary() method')  # noqa


class BCryptSHA256PasswordHasher(BasePasswordHasher):
    """Secure password hashing using the bcrypt algorithm
    """
    algorithm = "bcrypt_sha256"
    digest = hashlib.sha256
    library = ('bcrypt', 'bcrypt')
    rounds = 12

    def salt(self):
        bcrypt = self._load_library()
        return bcrypt.gensalt(rounds=self.rounds)

    def encode(self, password, salt):
        bcrypt = self._load_library()
        if self.digest is not None:
            password = binascii.hexlify(
                self.digest(password).digest())

        data = bcrypt.hashpw(password, salt)
        return "%s$%s" % (self.algorithm, data)

    def verify(self, password, encoded):
        algorithm, data = encoded.split('$', 1)
        assert algorithm == self.algorithm
        bcrypt = self._load_library()

        if self.digest is not None:
            password = binascii.hexlify(
                self.digest(password).digest())

        hashpw = bcrypt.hashpw(password, data)

        return constant_time_compare(data, hashpw)

    def safe_summary(self, encoded):
        algorithm, empty, algostr, work_factor, data = encoded.split('$', 4)
        assert algorithm == self.algorithm
        salt, checksum = data[:22], data[22:]
        return OrderedDict([
            ('algorithm', algorithm),
            ('work factor', work_factor),
            ('salt', mask_hash(salt)),
            ('checksum', mask_hash(checksum)),
        ])


class BCryptPasswordHasher(BCryptSHA256PasswordHasher):
    """Secure password hashing using the bcrypt algorithm

    This hasher does not first hash the password which means it is subject to
    the 72 character bcrypt password truncation, most use cases should prefer
    the BCryptSha512PasswordHasher.
    """
    algorithm = 'bcrypt'
    digest = None
