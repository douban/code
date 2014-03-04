define(
    ['jquery', 'backbone', 'underscore'],
    ($, Backbone, _) ->
        MenuItem = Backbone.Model.extend({
            defaults:
                id: 0
                name: ''
                title: ''
                href: '#'
                active: 0
        })
        return MenuItem
)

