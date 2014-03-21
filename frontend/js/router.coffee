define(
  ['jquery',
  'backbone',
  'underscore',
  'vilya/app',
  'modules/url',
  'views/page_views/home',
  'views/page_views/login',
  'views/page_views/explore',
  'views/page_views/projects/index',
  'views/page_views/projects/commits'],
  ($, Backbone, _, app, UrlUtil, HomeView, LoginView, ExploreView, ProjectIndexView,
  ProjectCommitsView) ->
    VILYA_ROOT = '/vilya/'

    class AppRouter extends Backbone.Router
      routes:
        "" : "showHome"
        "login" : "showLogin"
        "about" : "showAbout"
        "explore": "showExpore"
        ":user/:project": "showProject"
        ":user/:project/commits": "showProjectCommits"
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
      showLogin: () ->
        window.v = new LoginView(app.currentUser)
        this.loadView(v)
      showHome: () ->
        this.loadView(new HomeView())
      showExpore: () ->
        this.loadView(new ExploreView())
      showProject: (user, project) ->
        this.loadView(new ProjectIndexView({full_name: user + "/" + project}))
      showProjectCommits: (user, project) ->
        page = UrlUtil.getURLParameter('page')
        this.loadView(new ProjectCommitsView({full_name: user + "/" + project, page: page}))

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
