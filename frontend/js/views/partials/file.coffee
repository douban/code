define(
  ['jquery', 'backbone', 'handlebars', 'collections/project/files'],
  ($, Backbone, Handlebars, ProjectFiles) ->
    TreeFileView = Backbone.View.extend({
      template: Handlebars.compile($('#treeFileTemplate').html())
      initialize: (options) ->
        this.full_name =  options.full_name
        this.fileCollection = new ProjectFiles({full_name: this.full_name})
        this.fileCollection.fetch({reset: true})
        this.listenTo(this.fileCollection, 'reset', this.render)
      render: () ->
        this.$el.html(this.template({files: this.fileCollection.toJSON()}))
        $("#project-tree").html(@el)
      typeToDisplayClass: (type) ->
        {
          tree: "glyphicon-folder-close"
          blob: "glyphicon-file"
          file: "glyphicon-credit-card"
        }[type]
    })
    return TreeFileView
)
