define(
  ['jquery', 'backbone', 'underscore',
  'collections/projects',
  'views/project/card'],
  ($, Backbone, _, Projects, ProjectCardView) ->
    ExploreView = Backbone.View.extend({
      tagName: 'div'
      initialize: () ->
        $("#content").html(this.el)
        # FIXME: delete collection
        this.collection = new Projects()
        this.collection.fetch({reset: true})
        this.render()
        this.listenTo(this.collection, 'reset', this.render)
      render: () ->
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


