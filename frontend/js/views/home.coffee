define(
  ['jquery',
  'backbone',
  'handlebars'],
  ($, Backbone, Handlebars) ->
    HomeView = Backbone.View.extend({
      tagName: 'div'
      template: Handlebars.compile($('#homeTemplate').html())
      initialize: () ->
        $("#content").html(this.el)
        this.render()
      render: () ->
        this.$el.html(this.template())
        return this
    })
    return HomeView
)

