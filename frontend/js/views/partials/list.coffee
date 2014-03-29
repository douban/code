define(
  ['jquery', 'backbone', 'handlebars', 'collections/projects'],
  ($, Backbone, Handlebars, Projects) ->
    ProjectListView = Backbone.View.extend({
      collection: new Projects()
      template: Handlebars.compile($('#projectListTemplate').html())
      initialize: () ->
        @listenTo(@collection, 'reset', @render)
        @collection.fetch({reset: true})
      render: () ->
        @$el.html(this.template(projects:this.collection.toJSON()))
    })
)

