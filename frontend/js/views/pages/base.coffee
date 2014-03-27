define(
  ['jquery',
  'backbone',
  'handlebars'],
  ($, Backbone, Handlebars) ->
    PageView = Backbone.View.extend(
      el: "#content"
      _initialize: () ->
      _render: () ->
      initialize: (options) ->
        @_initialize(options)
        @render()
      render: (options) ->
        #@closePrevPage()
        @_render(options)
        @setCurrentPage()
      setCurrentPage: () ->
        app.currentPage = this
      closePrevPage: () ->
        if (app.currentPage)
          if (app.currentPage.closeView)
            app.currentPage.closeView()
          else
            app.currentPage.remove()
    )
    return PageView
)

