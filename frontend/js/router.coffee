define(
  ['jquery',
  'backbone',
  'underscore',
  'modules/url',
  'views/pages/home',
  'views/pages/login',
  'views/pages/logout',
  'views/pages/signup',
  'views/pages/explore',
  'views/pages/projects/show',
  'views/pages/projects/commits'],
  ($, Backbone, _, UrlUtil,
  HomeView, LoginView, LogoutView, SignupView, ExploreView, ProjectShowView, ProjectCommitsView) ->

    class Router extends Backbone.Router
      routes:
        "" : "showHome"
        "login" : "showLogin"
        "signup" : "showSignup"
        "logout" : "showLogout"
        "about" : "showAbout"
        "explore": "showExpore"
        ":user/:project": "showProject"
        ":user/:project/commits": "showProjectCommits"
      initialize: () ->
      showLogin: () -> new LoginView()
      showLogout: () -> new LogoutView()
      showSignup: () -> new SignupView()
      showHome: () -> new HomeView()
      showExpore: () -> new ExploreView()
      showProject: (user, project) -> new ProjectShowView({full_name: user + "/" + project})
      showProjectCommits: (user, project) ->
        page = UrlUtil.getURLParameter('page')
        new ProjectCommitsView({full_name: user + "/" + project, page: page})

    return Router
)
