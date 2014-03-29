define(
  ['jquery', 'backbone', 'handlebars', 'collections/project/commits'],
  ($, Backbone, Handlebars, ProjectCommits) ->
    CommitsView = Backbone.View.extend({
      template: Handlebars.compile($('#commitTemplate').html())
      initialize: (options) ->
        @full_name = options.project.get('full_name')
        @collection = new ProjectCommits({
          full_name: @full_name
          page: options.page
        })
        @collection.fetch({reset: true})
        @listenTo(@collection, 'reset', @render)
      render: () ->
        @$el.html(@template(commits: @collection.toJSON()))
    })
)
