define(
  ['jquery', 'backbone', 'handlebars', 'collections/project/commits'],
  ($, Backbone, Handlebars, ProjectCommits) ->
    CommitsView = Backbone.View.extend({
      template: Handlebars.compile($('#commitTemplate').html())
      initialize: (options) ->
        @collection = new ProjectCommits({
          full_name: options.full_name
          page: options.page
        })
        @collection.fetch({reset: true})
        @listenTo(@collection, 'reset', @render)
      render: () ->
        @$el.html(@template(commits: @collection.toJSON()))
    })
)
