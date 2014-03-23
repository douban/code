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
        "submit form":   "createCurrentUser"
      _render: () ->
        this.$el.html(this.template())
      createCurrentUser: (event) ->
        event.preventDefault()
        attrs =
          password: $(@el).find('#loginPassowrd').val()
          name: $(@el).find('#loginName').val()
        @model.save attrs,
                    success: () ->
                      app.router.navigate("", {trigger: true})
                      app.currentUser.unset('password')

    })
    return LoginView
)

