define('jquery-pullToRefresh', ['jquery'], 'lib/jquery.plugin.pullToRefresh.js');
require(['jquery', 'jquery-pullToRefresh'],
        function($){
            $(function () {
                  var timeline = $('.timeline dl'), isPublic = $('#is-public-timeline').val() == 'True' ? true : false;
                  var loadNews = function (defer) {
                      $.ajax({url:'/m/actions',
                              data:{since_id:timeline.children().first().attr('id') || '',
                                    is_public:isPublic},
                              dataTyep:'html',
                              success:function (r) {
                                  timeline.prepend(r);
                                  defer && defer.resolve();
                              }});
                  };
                  loadNews();

                  $('.scrollable').pullToRefresh(
                      {callback:function() {
                           var def = $.Deferred();
                           loadNews(def);
                           return def.promise();
                       }});
              });
        });