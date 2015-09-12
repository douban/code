# -*- coding: utf-8 -*-
import logging
import yaml

logger = logging.getLogger(__name__)
warn = logger.warn

DEFAULT_PROJECT_CONF = 'default_code_config.yaml'
PROJECT_CONF_FILE = 'code_config.yaml'


def _get_default_project_conf():
    with open(DEFAULT_PROJECT_CONF, 'r') as default_conf_file:
        default_conf_stream = default_conf_file.read()
    default_conf = yaml.load(default_conf_stream)
    return default_conf


class CodeConf(object):

    def __init__(self, project):
        self.project = project
        self._config = None

    @property
    def builders(self):
        return get_project_builders(self.project)

    @property
    def exists(self):
        repo = self.project.repo
        blob = repo.get_file('HEAD', PROJECT_CONF_FILE)
        if blob:
            return True

    @property
    def as_dict(self):
        if not self._config:
            project = self.project
            self._config = make_project_conf(project.name, project.repo)
        return self._config


def make_project_conf(project_name, repo):
    DEFAULT_PROJECT_CONF_CACHE = _get_default_project_conf()
    assert isinstance(DEFAULT_PROJECT_CONF_CACHE, dict), \
        "default conf needs to be a dict"
    default_conf = {}
    default_conf.update(DEFAULT_PROJECT_CONF_CACHE)

    blob = repo.get_file('HEAD', PROJECT_CONF_FILE)
    conf_stream = blob.data if blob else ''
    try:
        conf = yaml.load(conf_stream)
    except yaml.error.YAMLError, err:
        raise Exception("Project config yaml has an error: %s" % err)
    conf = conf if conf else {}
    assert isinstance(conf, dict), \
        "project conf YAML stream must be a dict: %s" % conf_stream

    return _merge_conf_into_default_conf(project_name, conf, default_conf)


def _merge_conf_into_default_conf(project_name, conf, default_conf):
    for key in conf:
        if key not in default_conf:
            warn("%s Configuration key rejected: %s, maybe add it to %s" %
                 (project_name, key, DEFAULT_PROJECT_CONF))
            continue
        default_conf[key] = conf[key]
    return default_conf


def get_project_builders(project):
    if not project.conf:
        return []
    blds = [(v.get('sort'), k) for k, v in project.conf['docs'].items()]
    blds = sorted(blds)
    blds = [_[1] for _ in blds]
    return blds
