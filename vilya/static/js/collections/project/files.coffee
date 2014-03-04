define(
    ['jquery', 'backbone', 'underscore',
    'models/git/object'],
    ($, Backbone, _, GitObject) ->
        ProjectFiles = Backbone.Collection.extend({
            model: GitObject
            url: () ->
                return '/api/v1/projects/' + this.full_name + '/files/'
            initialize: (options) ->
                this.full_name = options.full_name
        })
        return ProjectFiles
)
