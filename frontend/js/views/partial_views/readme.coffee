define(
  ['jquery', 'backbone', 'handlebars'],
  ($, Backbone, Handlebars) ->

    ReadmeView = Backbone.View.extend({
      template: Handlebars.compile($('#readmeTemplate').html())
      render: () ->
        this.$el.html(this.template(this.model.toJSON()))
        return this
    })
    return ReadmeView
)
