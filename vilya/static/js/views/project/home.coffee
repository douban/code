define(
    ['jquery', 'backbone', 'underscore',
    'models/project',
    'collections/project/files',
    'views/tree/file'],
    ($, Backbone, _, Project, ProjectFiles, TreeFileView) ->
        ProjectHomeView = Backbone.View.extend({
            tagName: 'div'
            initialize: (options) ->
                $("#content").html(this.el);
                full_name = options.full_name
                #this.project = new Project({full_name: full_name})
                #this.project.fetch()
                this.fileCollection = new ProjectFiles({full_name: full_name})
                this.fileCollection.fetch({reset: true})
                this.listenTo(this.fileCollection, 'reset', this.render)
            render: () ->
                this.views = this.fileCollection.map(
                    (item) ->
                        return this.renderFile(item);
                    ,
                    this
                )
            renderFile: (item) ->
                view = new TreeFileView({
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
        return ProjectHomeView
)
