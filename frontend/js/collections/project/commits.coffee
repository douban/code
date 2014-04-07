define(
  ['jquery', 'backbone', 'underscore',
  'models/git/commit'],
  ($, Backbone, _, GitCommit) ->
    ProjectCommits = Backbone.Collection.extend({
      model: GitCommit
      url: () ->
        return "/api/v1/projects/#{@full_name}/commits/?#{$.param(page: @page)}"
      initialize: (options) ->
        if options.page != undefined
          @page = options.page
        else
          @page = 1
        @full_name = options.full_name
      fetchPage: (page) ->
        @page = page
        @fetch({reset: true, success: -> callback?()})
    })
    return ProjectCommits
)
