define(
    ['jquery', 'backbone', 'underscore'],
    ($, Backbone, _) ->
        Tree = Backbone.Model.extend({
            defaults:
                id: 0
                type: 'tree'
                name: ''
        })
        return Tree
)
