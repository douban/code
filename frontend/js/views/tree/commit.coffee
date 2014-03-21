define(
  ['jquery', 'backbone', 'handlebars'],
  ($, Backbone, Handlebars) ->

    CommitView = Backbone.View.extend({
      template: Handlebars.compile($('#commitTemplate').html())
      render: () ->
        this.$el.html(this.template(this.model.toJSON()))
        return this
    })
    return CommitView
)
