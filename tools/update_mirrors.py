# -*- coding: utf-8 -*-

import sys
from traceback import print_exc
from vilya.models.consts import MIRROR_STATE_CLONED
from vilya.models.mirror import CodeDoubanMirror
from vilya.models.project import CodeDoubanProject


def main():
    try:
        mirror_projects = CodeDoubanProject.get_projects(owner='mirror', sortby='created')
        for project in mirror_projects:
            mirror = CodeDoubanMirror.get_by_project_id(project.id)
            if not mirror:
                print "New: ", project.id, project.name, project.url
                mirror_url = project.git.call('ls-remote --get-url origin')
                CodeDoubanMirror.add(mirror_url, MIRROR_STATE_CLONED, project.id)
            else:
                print "Added: ", project.id, project.name, project.url
    except Exception, e:
        print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
