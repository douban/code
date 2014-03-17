define(
  ['jquery', 'backbone', 'underscore'],
  ($, Backbone, _) ->
    _.templateSettings = {
      evaluate: /\{\{([\s\S]+?)\}\}/g
      interpolate: /\{\{=([\s\S]+?)\}\}/g
      escape: /\{\{-([\s\S]+?)\}\}/g
    }

    TreeFileView = Backbone.View.extend({
      template: _.template($('#treeFileTemplate').html())
      render: () ->
        this.$el.html(this.template(this.model.toJSON()))
        return this
    })
    return TreeFileView
)
