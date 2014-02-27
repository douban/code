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
            url: '/api/projects/' + this.full_name + '/'
        })
        return Project
)
