define(
    ['jquery',
    'backbone',
    'underscore',
    'vilya/app',
    'views/home',
    'views/explore'],
    ($, Backbone, _, app, HomeView, ExploreView) ->
        VILYA_ROOT = '/vilya/'

        class AppRouter extends Backbone.Router
            routes:
                "" : "showHome"
                "about" : "showAbout"
                "explore": "showExpore"
                #":user/:project": "",
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
                console.log "about"
            showHome: () ->
                this.loadView(new HomeView())
                console.log "about"
            showExpore: () ->
                this.loadView(new ExploreView())
                console.log "projects"

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
