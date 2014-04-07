define(
  ['jquery',
  'views/pages/base',
  'handlebars'],
  ($, PageView, Handlebars) ->
    LoginView = PageView.extend({
      _initialize: () ->
        @model = app.currentUser
        @model.destroy success: ->
                         app.currentUser.clear()
                         app.router.navigate("", {trigger: true})
      _render: () ->
    })
)

