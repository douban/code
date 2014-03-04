define(
    ['jquery', 'backbone', 'underscore',
    'models/project',
    'collections/project/commits',
    'views/tree/commit',
    'views/tree/menu'],
    ($, Backbone, _, Project, ProjectCommits, CommitView, MenuView) ->
        ProjectCommitsView = Backbone.View.extend({
            tagName: 'div'
            className: 'row'
            initialize: (options) ->
                $("#content").html(this.el);
                this.full_name = options.full_name
                this.fileCollection = new ProjectCommits({
                    full_name: this.full_name
                    page: options.page
                })
                this.fileCollection.fetch({reset: true})
                this.listenTo(this.fileCollection, 'reset', this.render)
            render: () ->
                this.$el.append('<div id="project-menu" class="col-sm-2"></div><div id="project-content" class="col-sm-10"></div>')
                this.menuView = this.renderMenu()
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
                $el = this.$el.find('#project-content')
                $el.append(view.render().el);
                return view
            renderMenu: () ->
                view = new MenuView({full_name: this.full_name})
                $el = this.$el.find('#project-menu')
                $el.append(view.render().el);
                return view
            closeView: () ->
                _.each(this.views, (view) ->
                    view.remove()
                )
                this.menuView.closeView()
                this.remove()
        })
        return ProjectCommitsView
)

