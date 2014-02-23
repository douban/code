define(
    ['jquery', 'backbone', 'underscore'],
    ($, Backbone, _) ->
        Blob = Backbone.Model.extend({
            defaults:
                id: 0
                type: 'blob'
                name: ''
        })
        return Blob
)
