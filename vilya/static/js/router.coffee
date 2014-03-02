define(
    ['jquery',
    'backbone',
    'underscore',
    'vilya/app',
    'views/home',
    'views/explore',
    'views/project/home'],
    ($, Backbone, _, app, HomeView, ExploreView, ProjectHomeView) ->
        VILYA_ROOT = '/vilya/'

        class AppRouter extends Backbone.Router
            routes:
                "" : "showHome"
                "about" : "showAbout"
                "explore": "showExpore"
                ":user/:project": "showProject"
                #":user/:project/commits": "",
            initialize: (app) ->
                this.app = app
                this.loadView(new HomeView())
            loadView: (view) ->
                if (this.view)
                    if (this.view.closeView)
                        this.view.closeView()
                    else
                        this.view.remove()
                this.view = view
            showAbout: () ->
                this.loadView(new HomeView())
            showHome: () ->
                this.loadView(new HomeView())
            showExpore: () ->
                this.loadView(new ExploreView())
            showProject: (user, project) ->
                this.loadView(new ProjectHomeView({full_name: user + "/" + project}))

        initialize = (app) ->
            app.router = new AppRouter()
            Backbone.history.start({
                #pushState: true,
                #root: VILYA_ROOT
            })

        return {
            initialize: initialize
        }
)
