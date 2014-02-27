define(
    ['jquery', 'backbone', 'underscore', 'collections/projects', 'views/project'],
    ($, Backbone, _, Projects, ProjectView) ->
        ExploreView = Backbone.View.extend({
            tagName: 'div'
            initialize: () ->
                $("#content").html(this.el);
                this.views = []
                # FIXME: delete collection
                this.collection = new Projects()
                this.collection.fetch({reset: true})
                this.render()
                this.listenTo(this.collection, 'reset', this.render)
            render: () ->
                this.collection.each(
                    (item) ->
                        this.renderProject(item);
                    ,
                    this
                )
                console.log this.views
            renderProject: (item) ->
                projectView = new ProjectView({
                    model: item
                })
                this.$el.append(projectView.render().el);
                this.views.push(projectView)
            closeView: () ->
                _.each(this.views, (view) ->
                    view.remove()
                )
                this.remove()
        })
        return ExploreView
)


