define(
  ['jquery',
  'backbone',
  'handlebars'],
  ($, Backbone, Handlebars) ->
    LoginView = Backbone.View.extend({
      tagName: 'div'
      template: Handlebars.compile($('#loginTemplate').html())
      initialize: (currentUser) ->
        @model = currentUser
        $("#content").html(@el)
        this.render()
      render: () ->
        this.$el.html(this.template())
        return this
      events:
        "submit form":   "createLogin"
      createLogin: (event) ->
        event.preventDefault()
        @model.set('password', $(@el).find('#loginPassowrd').val())
        @model.set('name', $(@el).find('#loginName').val())
        @model.save()
    })
    return LoginView
)

