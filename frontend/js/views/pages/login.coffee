define(
  ['jquery',
  'views/pages/base',
  'handlebars'],
  ($, PageView, Handlebars) ->
    LoginView = PageView.extend({
      tagName: 'div'
      template: Handlebars.compile($('#loginTemplate').html())
      _initialize: () ->
        @model = app.currentUser
      events:
        "submit form":   "createLogin"
      _render: () ->
        this.$el.html(this.template())
      createLogin: (event) ->
        event.preventDefault()
        @model.set('password', $(@el).find('#loginPassowrd').val())
        @model.set('name', $(@el).find('#loginName').val())
        @model.save()
    })
    return LoginView
)

