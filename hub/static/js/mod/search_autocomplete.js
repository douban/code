define('mod/search_autocomplete', [
    'jquery'
], function($) {
    var keyCode = {enter:13, esc:27, tab:9, up:38, down:40, ctrl:17, n:78, p:80};
    var searchInput = $('#global-search-field'), search_repos_menu,
    hideReposMenu = function () {
        search_repos_menu && !searchInput.is(":focus")
            && !search_repos_menu.is(":focus") && search_repos_menu.empty().hide();
    },
    showIntro = function () {
        if (!search_repos_menu || search_repos_menu.is(':empty')) {
            var introContent = '<ul><li class="intro">Input project name to search <b>project</b> or startswith <span style="color:#4183C4">"@"</span> to search <b>user</b>.</li></ul>';
            search_repos_menu = $('<div id="search-repos-menu"></div>').appendTo('#search')
                .on('mouseenter', 'li', function () {
                    search_repos_menu.find('li.active').removeClass('active');
                    $(this).addClass('active');
                })
                .on('click', 'li', function (e) {
                    e.preventDefault();
                    var url = $(this).attr('data-url');
                    url && (window.location.href = url);
                });
            search_repos_menu.html(introContent).show();
        }
    };
    $('body').click(function () {setTimeout(hideReposMenu, 100);});
    searchInput
        .focusin(showIntro)
        .keydown(function (e) {
            (e.keyCode == keyCode.enter && search_repos_menu && search_repos_menu.find('li.active').length) && e.preventDefault();
        })
        .keyup(
          function (e) {
              var k = e.keyCode;
              if (k == keyCode.up || k == keyCode.down || k == keyCode.n
                  || k == keyCode.p || k == keyCode.ctrl || k == keyCode.enter) {
                  if (search_repos_menu && search_repos_menu.find('li').length) {
                      (k == keyCode.esc) && hideReposMenu();// esc key to close the menu
                      var actItem = search_repos_menu.find('li.active');
                      if (actItem.length) {
                          var a = actItem;
                          if (k == keyCode.up ||
                              (k == keyCode.p  && e.ctrlKey == true)) { // up
                              var p = a.removeClass('active').prev();
                              (p.length ? p : search_repos_menu.find('li:last')).addClass('active');
                          } else if (k == keyCode.down ||
                                     (k == keyCode.n  && e.ctrlKey == true)) { // down
                              var n = a.removeClass('active').next();
                              (n.length ? n : search_repos_menu.find('li:first')).addClass('active');
                          } else if (k == keyCode.enter) { // enter key to go to repo
                              e.preventDefault();
                              var url = actItem.attr('data-url');
                              url && (window.location.href = url);
                          }
                      } else {
                          search_repos_menu.find('li:first').addClass('active');
                      }
                  }
              } else {
                  var q = $(this).val(), reqUrl, templ;
                  if (q.substr(0, 1) == '@') {
                      // search for users
                      q = q.substring(1);
                      reqUrl = '/api/autocomplete_users';
                      templ = $('#templ-users-autocomplete');
                  } else {
                      // search for repos
                      reqUrl = '/api/autocomplete_repos';
                      templ = $('#templ-repos-autocomplete');
                  }
                  (q != '') ? $.getJSON(reqUrl,
                                        {q:q},
                                        function (r) {
                                            var current_q = searchInput.val();
                                            if (current_q === q) {
                                                search_repos_menu.html($.tmpl(templ, r)).show();
                                            }
                                        }) : showIntro();
              }
          });

});
