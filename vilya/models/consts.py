# -*- coding: utf-8 -*-


PULL_REF_H = 'refs/pull/%s/head'
PULL_REF_M = 'refs/pull/%s/merge'

# line comment
LINECOMMENT_INDEX_EMPTY = -1
LINECOMMENT_INDEX_INVALID = -2  # 用于没有 linenum 的旧数据

LINECOMMENT_TYPE_COMMIT = 1
LINECOMMENT_TYPE_PULL = 2

PATCH_TYPE = {
    "A": "added",
    "D": "removed",
    "M": "modified",
    "R": "renamed",
}
