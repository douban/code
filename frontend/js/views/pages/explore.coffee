define([
  'jquery',
  'views/pages/base',
  'underscore',
  'collections/projects',
  'views/partials/card'],
  ($, PageView, _, Projects, ProjectCardView) ->
    ExploreView = PageView.extend({
      _initialize: () ->
        # FIXME: delete collection
        @collection = new Projects()
        @collection.fetch({reset: true})
        @listenTo(@collection, 'reset', @render)
      _render: () ->
        @views = @collection.map(
          (item) ->
            return @renderProject(item)
          ,
          this
        )
      renderProject: (item) ->
        projectCardView = new ProjectCardView({
          model: item
        })
        @$el.append(projectCardView.render().el)
        return projectCardView
      closeView: () ->
        _.each(@views, (view) ->
          view.remove()
        )
        @remove()
    })
)


