define(
  ['jquery', 'backbone', 'handlebars'],
  ($, Backbone, Handlebars) ->
    TreeFileView = Backbone.View.extend({
      template: Handlebars.compile($('#treeFileTemplate').html())
      render: () ->
        fileData = this.model.toJSON()
        fileData.display_class = this.typeToDisplayClass(fileData.type)
        this.$el.html(this.template(fileData))
        return this
      typeToDisplayClass: (type) ->
        {
          tree: "glyphicon-folder-close"
          blob: "glyphicon-file"
          file: "glyphicon-credit-card"
        }[type]
    })
    return TreeFileView
)
