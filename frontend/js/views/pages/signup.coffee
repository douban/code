define(
  ['jquery',
  'backbone',
  'models/user',
  'views/pages/base',
  'handlebars'],
  ($, Backbone, User, PageView, Handlebars) ->
    SignupView = PageView.extend({
      template: Handlebars.compile($('#signupTemplate').html())
      _initialize: () ->
      events:
        "submit form":   "createUser"
      _render: () ->
        @$el.html(this.template())
      createUser: (event) ->
        event.preventDefault()
        @model = new User()
        attrs =
          password: $(@el).find('#signupPassowrd').val()
          email: $(@el).find('#signupEmail').val()
          name: $(@el).find('#signupName').val()
        @model.save(attrs,
                    success: () ->
                      app.currentUser.fetch()
                      app.router.navigate("", {trigger: true})
        )
    })
)

