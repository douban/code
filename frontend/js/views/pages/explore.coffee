define([
  'jquery',
  'views/pages/base',
  'underscore',
  'collections/projects',
  'views/partials/card'],
  ($, PageView, _, Projects, ProjectCardView) ->
    ExploreView = PageView.extend({
      tagName: 'div'
      _initialize: () ->
        # FIXME: delete collection
        this.collection = new Projects()
        this.collection.fetch({reset: true})
        this.listenTo(this.collection, 'reset', this.render)
      _render: () ->
        this.views = this.collection.map(
          (item) ->
            return this.renderProject(item)
          ,
          this
        )
      renderProject: (item) ->
        projectCardView = new ProjectCardView({
          model: item
        })
        this.$el.append(projectCardView.render().el)
        return projectCardView
      closeView: () ->
        _.each(this.views, (view) ->
          view.remove()
        )
        this.remove()
    })
    return ExploreView
)


