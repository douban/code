define(
  ['jquery', 'backbone', 'handlebars'],
  ($, Backbone, Handlebars) ->
    TreeFileView = Backbone.View.extend({
      template: Handlebars.compile($('#treeFileTemplate').html())
      render: () ->
        this.$el.html(this.template(this.model.toJSON()))
        return this
    })
    return TreeFileView
)
