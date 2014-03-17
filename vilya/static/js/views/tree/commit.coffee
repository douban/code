define(
  ['jquery', 'backbone', 'underscore'],
  ($, Backbone, _) ->
    _.templateSettings = {
      evaluate: /\{\{([\s\S]+?)\}\}/g
      interpolate: /\{\{=([\s\S]+?)\}\}/g
      escape: /\{\{-([\s\S]+?)\}\}/g
    }

    CommitView = Backbone.View.extend({
      template: _.template($('#commitTemplate').html())
      render: () ->
        this.$el.html(this.template(this.model.toJSON()))
        return this
    })
    return CommitView
)
