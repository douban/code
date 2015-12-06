# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)


class SearchClientStub(object):

    def __init__(self, *a, **kw):
        pass

    def __getattr__(self, attr):
        logger.info("%s.%s is called" % (self.__class__.__name__, attr))
        return self.__init__


class MQPoolStub(object):

    def __init__(self, *a, **kw):
        pass

    def __getattr__(self, attr):
        logger.info("%s.%s is called" % (self.__class__.__name__, attr))
        return self.__init__
