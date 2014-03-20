define(
  ['jquery',
  'backbone',
  'underscore',
  'vilya/app',
  'modules/url',
  'models/login',
  'views/home',
  'views/login',
  'views/explore',
  'views/project/home',
  'views/project/commits'],
  ($, Backbone, _, app, UrlUtil, Login, HomeView, LoginView, ExploreView, ProjectHomeView,
  ProjectCommitsView) ->
    VILYA_ROOT = '/vilya/'
    window.Login = Login

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
        this.loadView(new LoginView())
      showHome: () ->
        this.loadView(new HomeView())
      showExpore: () ->
        this.loadView(new ExploreView())
      showProject: (user, project) ->
        this.loadView(new ProjectHomeView({full_name: user + "/" + project}))
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
