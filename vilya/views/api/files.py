from vilya.libs import api_errors
from quixote.errors import TraversalError
from vilya.views.api.utils import jsonize

from ellen.utils import JagareError


class FileResolveUI(object):
    _q_exports = []

    def __init__(self, ret):
        self._ret = ret

    def __call__(self, request):
        return self._ret

    def _q_index(self, request):
        return self._ret

    def _q_lookup(self, request, path):
        return self


class FilesUI(object):
    _q_exports = []

    def __init__(self, request, project):
        self._project = project

    def __call__(self, request):
        return self._index(request)

    def q_index(self, request):
        return self._index(request)

    @jsonize
    def _index(self, request, path=None):
        project = self._project
        ref = request.get_form_var('ref') or project.default_branch
        path = path or request.get_form_var('path') or ''
        tree = None
        file_ = None
        type_ = None
        readme = None

        try:
            recursive = bool(request.get_form_var('recursive'))
            tree = project.repo.get_tree(ref, path, recursive=recursive,
                                         recursive_with_tree_node=True)
            type_ = "tree"
        except JagareError, e:
            if "Reference not found" in str(e):
                raise api_errors.NotFoundError
            else:
                raise e
        except TypeError:
            file_ = project.repo.get_file(ref, path)
            type_ = "blob"
        except KeyError:
            submodule = project.repo.get_submodule(ref, path)
            if submodule:
                return submodule.as_dic()

        if type_ == "tree":
            if isinstance(tree, basestring):
                raise TraversalError("Got a blob instead of a tree")
            for item in tree:
                if item['type'] == "blob" and item['name'].startswith('README'):  # noqa
                    readme = project.repo.get_file(ref, item["path"]).data
                    break
        elif not file_:
            raise TraversalError("file not found")

        dic = {"ref": ref,
               "type": type_,
               "content": (tree.entries if type_ == "tree" \
                           else file_.data.encode('utf8'))}

        if readme:
            dic["readme"] = readme
        return dic

    def _q_lookup(self, request, path):
        path = request.get_path().decode('utf8')
        path_components = path.split('/')
        path_components.reverse()
        while path_components and path_components.pop() != "files":
            continue
        path_components.reverse()
        path = '/'.join(path_components)
        return FileResolveUI(self._index(request, path))
