define(
  ['jquery', 'backbone', 'handlebars', 'collections/project/files'],
  ($, Backbone, Handlebars, ProjectFiles) ->
    FilesView = Backbone.View.extend({
      template: Handlebars.compile($('#projectBasicTemplate').html())
      initialize: (options) ->
        @setElement(options.el)
        @full_name =  options.full_name
        @collection = new ProjectFiles({full_name: @full_name})
        @listenTo(@collection, 'reset', @render)
        @collection.fetch({reset: true})
      render: () ->
        @$el.html(@template({files: @collection.toJSON()}))
      typeToDisplayClass: (type) ->
        {
          tree: "glyphicon-folder-close"
          blob: "glyphicon-file"
          file: "glyphicon-credit-card"
        }[type]
    })
)
