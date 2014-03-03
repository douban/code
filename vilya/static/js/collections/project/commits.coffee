define(
    ['jquery', 'backbone', 'underscore',
    'models/git/commit'],
    ($, Backbone, _, GitCommit) ->
        ProjectCommits = Backbone.Collection.extend({
            model: GitCommit
            url: () ->
                return '/api/v1/projects/' + this.full_name + '/commits/'
            initialize: (options) ->
                this.full_name = options.full_name
        })
        return ProjectCommits
)

