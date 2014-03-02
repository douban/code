define(
    ['jquery', 'backbone', 'underscore'],
    ($, Backbone, _) ->
        GitObject = Backbone.Model.extend({
            defaults:
                id: 0
                type: 'tree'
                name: ''
                mode: ''
        })
        return GitObject
)
