define(
  ['jquery', 'backbone', 'handlebars'],
  ($, Backbone, Handlebars) ->
    ProjectCardView = Backbone.View.extend({
      tagName: 'div'
      className: 'projectContainer'
      template: Handlebars.compile($('#projectTemplate').html())
      render: () ->
        this.$el.html(this.template(this.model.toJSON()))
        return this
    })
    return ProjectCardView
)

