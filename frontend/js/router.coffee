define(
  ['jquery',
  'backbone',
  'underscore',
  'modules/url',
  'views/pages/home',
  'views/pages/login',
  'views/pages/explore',
  'views/pages/projects/index',
  'views/pages/projects/commits'],
  ($, Backbone, _, UrlUtil, HomeView, LoginView, ExploreView, ProjectIndexView,
  ProjectCommitsView) ->

    class Router extends Backbone.Router
      routes:
        "" : "showHome"
        "login" : "showLogin"
        "about" : "showAbout"
        "explore": "showExpore"
        ":user/:project": "showProject"
        ":user/:project/commits": "showProjectCommits"
      initialize: () ->
      loadView: (view) ->
        this.view = view
      showLogin: () ->
        this.loadView(new LoginView())
      showHome: () ->
        this.loadView(new HomeView())
      showExpore: () ->
        this.loadView(new ExploreView())
      showProject: (user, project) ->
        this.loadView(new ProjectIndexView({full_name: user + "/" + project}))
      showProjectCommits: (user, project) ->
        page = UrlUtil.getURLParameter('page')
        this.loadView(new ProjectCommitsView({full_name: user + "/" + project, page: page}))

    return Router
)
