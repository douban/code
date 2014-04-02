define(
  ['jquery', 'backbone', 'handlebars', 'collections/project/files'],
  ($, Backbone, Handlebars, ProjectFiles) ->
    BasicView = Backbone.View.extend({
      template: Handlebars.compile($('#projectBasicTemplate').html())
      initialize: (options) ->
        @setElement(options.el)
        @project = options.project
        @collection = new ProjectFiles(full_name: @project.get("full_name"))
        @listenTo(@collection, 'reset', @render)
        @collection.fetch({reset: true})
        @listenTo(@project, 'change', @render)
      render: () ->
        @$el.html(@template(files: @collection.toJSON(), project: @project.toJSON()))
      typeToDisplayClass: (type) ->
        {
          tree: "glyphicon-folder-close"
          blob: "glyphicon-file"
          file: "glyphicon-credit-card"
        }[type]
    })
)
