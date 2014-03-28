define([
  'jquery'
  'views/pages/base'
  'handlebars'
  'models/project'
], ($, PageView, Handlebars, Project) ->
    # project new view don't inherit ProjectBaseView
    ProjectNewView = PageView.extend({
      template: Handlebars.compile($('#projectNewTemplate').html())
      _initialize: () ->
      events:
        "submit form":   "createProject"
      _render: () ->
        @$el.html(@template())
      createProject: (event) ->
        event.preventDefault()
        @model = new Project()
        attrs =
          name: @$el.find('#projectName').val()
          description: @$el.find('#projectDescription').val()
        @model.save attrs,
                    success: (model, json) ->
                      app.router.navigate("/#{model.get('full_name')}", {trigger: true})

    })
)

