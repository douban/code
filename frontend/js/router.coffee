define(
  ['jquery',
  'backbone',
  'underscore',
  'modules/url',
  'views/page_views/home',
  'views/page_views/login',
  'views/page_views/explore',
  'views/page_views/projects/index',
  'views/page_views/projects/commits'],
  ($, Backbone, _, UrlUtil, HomeView, LoginView, ExploreView, ProjectIndexView,
  ProjectCommitsView) ->

    class AppRouter extends Backbone.Router
      routes:
        "" : "showHome"
        "login" : "showLogin"
        "about" : "showAbout"
        "explore": "showExpore"
        ":user/:project": "showProject"
        ":user/:project/commits": "showProjectCommits"
      initialize: (app) ->
        @app = app
        app.router = this
      loadView: (view) ->
        if (this.view)
          if (this.view.closeView)
            this.view.closeView()
          else
            this.view.remove()
        this.view = view
      showLogin: () ->
        this.loadView(new LoginView(app.currentUser))
      showHome: () ->
        this.loadView(new HomeView())
      showExpore: () ->
        this.loadView(new ExploreView())
      showProject: (user, project) ->
        this.loadView(new ProjectIndexView({full_name: user + "/" + project}))
      showProjectCommits: (user, project) ->
        page = UrlUtil.getURLParameter('page')
        this.loadView(new ProjectCommitsView({full_name: user + "/" + project, page: page}))

    return AppRouter
)
