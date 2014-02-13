# -*- coding: utf-8 -*-
import os

CODE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def get_permdir():
    return os.path.join(CODE_DIR, 'permdir')


def get_repo_root():
    return get_permdir()


def get_tmpdir():
    return os.path.join(CODE_DIR, 'tmpdir')


def init_permdir():
    path = get_permdir()
    if not os.path.exists(path):
        os.makedirs(path)

init_permdir()
