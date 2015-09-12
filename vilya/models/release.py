# coding: utf8

import logging
import time
import sys
import pprint

import requests

from vilya.libs.store import mc, clear_local_cache, ONE_DAY

MC_KEY_REPOSITORY_RELEASE = 'latest_release:%s'
MC_KEY_UNRELEASE_COMMITS = 'release:%s:%s:%s:commits'


def get_release(repository):
    '''get latest successed release info

    return: a dict with keys {annotate, changesets, message, first_rev,
                              last_rev, pre_release_rev, status,
                              project_source, release_manger, release_time,
                              url}
    '''
    if not repository.startswith('http:'):
        repository = 'http://code.dapps.douban.com/' + repository
    if not repository.endswith('.git'):
        repository = repository + '.git'

    key = MC_KEY_REPOSITORY_RELEASE % repository
    info = mc.get(key)

    if info is not None:
        return info

    try:
        info = fetch_release(repository)
        mc.set(key, info, ONE_DAY)
        return info
    except:
        return {}


def fetch_release(repository):
    # TODO
    return {}


def get_unreleased_commit_num(project):
    last_release_info = get_release(project.repository)
    from_ref = last_release_info['last_rev'] if last_release_info else None
    key = MC_KEY_UNRELEASE_COMMITS % (project.id,
                                      project.default_sha,
                                      from_ref)
    num = mc.get(key)
    if num is None:
        commits = project.repo.get_commits(project.default_branch,
                                           from_ref=from_ref,
                                           max_count=100)
        num = len(commits)
        mc.set(key, num, ONE_DAY)
    return num


def expire_outdated_releases():
    '''TODO: 新代码上线后及时清理缓存
    '''


if __name__ == '__main__':
    if sys.argv[1:] and sys.argv[1] == 'expire':
        expire_outdated_releases()
    else:
        if sys.argv[1:]:
            resp = sys.argv[1]
        else:
            resp = 'http://code.dapps.douban.com/code.git'
        pprint.pprint(get_release(resp))
