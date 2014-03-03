define(
    ['jquery', 'backbone', 'underscore',
    'models/project',
    'collections/project/commits',
    'views/tree/commit'],
    ($, Backbone, _, Project, ProjectCommits, CommitView) ->
        ProjectCommitsView = Backbone.View.extend({
            tagName: 'div'
            initialize: (options) ->
                $("#content").html(this.el);
                full_name = options.full_name
                #this.project = new Project({full_name: full_name})
                #this.project.fetch()
                this.fileCollection = new ProjectCommits({full_name: full_name, page: options.page})
                this.fileCollection.fetch({reset: true})
                this.listenTo(this.fileCollection, 'reset', this.render)
            render: () ->
                this.views = this.fileCollection.map(
                    (item) ->
                        return this.renderCommit(item);
                    ,
                    this
                )
            renderCommit: (item) ->
                view = new CommitView({
                    model: item
                })
                this.$el.append(view.render().el);
                return view
            closeView: () ->
                _.each(this.views, (view) ->
                    view.remove()
                )
                this.remove()
        })
        return ProjectCommitsView
)

