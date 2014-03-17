define(
  ['jquery', 'backbone', 'underscore',
  'models/git/commit'],
  ($, Backbone, _, GitCommit) ->
    ProjectCommits = Backbone.Collection.extend({
      model: GitCommit
      url: () ->
        return '/api/v1/projects/' + this.full_name + '/commits/?' + $.param({page: this.page})
      initialize: (options) ->
        if options.page != undefined
          this.page = options.page
        else
          this.page = 1
        this.full_name = options.full_name
      fetchPage: (page) ->
        this.page = page
        this.fetch({reset: true, success: -> callback?()})
    })
    return ProjectCommits
)

