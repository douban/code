define(
  ['jquery',
  'backbone',
  'handlebars',
  'models/login'],
  ($, Backbone, Handlebars, Login) ->
    LoginView = Backbone.View.extend({
      tagName: 'div'
      template: Handlebars.compile($('#loginTemplate').html())
      initialize: () ->
        $("#content").html(this.el)
        this.render()
      render: () ->
        this.$el.html(this.template())
        return this
      events:
        "submit form":   "createLogin"
      createLogin: (event) ->
        event.preventDefault()
        login = new Login
        login.set('password', $(@el).find('#loginPassowrd').val())
        login.set('name', $(@el).find('#loginName').val())
        login.save()
    })
    return LoginView
)

