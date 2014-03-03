define(
    ['jquery', 'backbone', 'underscore'],
    ($, Backbone, _) ->
        Project = Backbone.Model.extend({
            defaults:
                id: 0
                description: ''
                name: ''
                full_name: ''
                owner_name: ''
                owner_id: 0
            urlRoot: '/api/v1/projects/'
            url: () ->
                this.full_name + '/'
        })
        return Project
)
