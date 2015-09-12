//define('jquery', 'lib/jquery.min.js')
//define('mustache', 'lib/mustache.js')
//define('bootstrap', 'lib/bootstrap-amd.js')
//define('jquery-tmpl', 'lib/jquery.tmpl.min.js')
//define('bootbox', 'lib/bootbox.js')
require(['jquery'
, 'mustache'
, 'mod/confirm'], function($, Mustache){

      $("div.trending-repositories a[href^='#tab_']").click(
          function(e) {
              tab_name = $(this).attr("href").slice("#tab_".length);
              $.ajax({type: "GET",
                      url: "/api/projects?without_commits=true&sortby=" + tab_name,
                      dataType: "json",
                      success: function(data){
                          var template = $("script#item-project").html();
                          var render = '<table class="table repo"><tbody>';

                          for(idx_proj in data['projects']){
                              proj = data['projects'][idx_proj];
                              render += Mustache.to_html(template, proj);
		                      if (idx_proj >= 5) { break }
                          }
	                      render += '</tbody></table>';
                          $("div#tab_" + tab_name).html(render);
                      }, 
                     });
          });

      $("div.repositories-by-dept a[href^='#proj_dept_']").click(
          function(e) {
              dept_name = $(this).attr("href").slice("#proj_dept_".length);
              $.ajax({type: "GET",
                      url: "/api/projects?without_commits=true&by_dept=" + dept_name,
                      dataType: "json",
                      success: function(data){
                          var template = $("script#item-project").html();
                          var render = '<table class="table repo"><tbody>';

                          for(idx_proj in data['projects']){
                              proj = data['projects'][idx_proj];
                              render += Mustache.to_html(template, proj);
                          }
	                      render += '</tbody></table>';
                          $("div#proj_dept_" + dept_name).html(render);
                      }
                     });
          });

    $("div.trending-repositories a[href='#tab_updated']").click();
    $("div.repositories-by-dept a[href='#proj_dept_public']").click();


});
