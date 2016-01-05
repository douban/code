
require.config({ enable_ozma: true });


/* @source mod/drop_down_list.js */;

define(
    'mod/drop_down_list',
    [
  "jquery"
],
    function($) {
        var addItemMenu = function (inputObj, success, introAppendTo, reqUrl, templ, menuType, successArg){
            var keyCode = {enter:13, esc:27, tab:9, up:38, down:40, ctrl:17, n:78, p:80},
            item_menu,
            get_data = function (url){
                if (menuType == "repos"){
                    length = url.length,
                    url = url.slice(1, length - 1);
                }else {
                    url = url.split('/')[2];
                }
                return url;
            },
            call_success = function (){
                if (menuType == "repos"){
                    success();
                } else {
                    success(successArg);
                    $(introAppendTo).find('.add-item-menu').remove();
                }
            };

            var hideAddItemMenu = function () {
                item_menu && item_menu.empty().remove();
            };

            var showIntro = function () {
                if (!item_menu || item_menu.is(':empty')) {
                    item_menu = $('<div class="add-item-menu"></div>').appendTo(introAppendTo)
                    .on('mouseenter', 'li', function () {
                        item_menu.find('li.active').removeClass('active');
                        $(this).addClass('active');
                    })
                    .on('click', 'li', function (e) {
                        e.preventDefault();
                        var url = $(this).attr('data-url');
                        url = get_data(url);
                        inputObj.val(url);
                        setTimeout(hideAddItemMenu, 100);
                        call_success();
                    });
                }
            };

            $('body').click(function () {setTimeout(hideAddItemMenu, 100);});

            inputObj.live('keydown', function (e) {
                (e.keyCode == keyCode.enter && item_menu && item_menu.find('li.active').length) && e.preventDefault();
                showIntro();
            }).live('keyup',
                  function (e) {
                      showIntro();
                      var k = e.keyCode;
                      if (k == keyCode.up || k == keyCode.down || k==keyCode.ctrl
                          || k == keyCode.enter || k == keyCode.p || k == keyCode.n){
                              if (item_menu && item_menu.find('li').length){
                                  (k == keyCode.esc) && hideAddItemMenu();// esc key to close the menu
                                  var actItem = item_menu.find('li.active');
                                  if (actItem.length) {
                                      var a = actItem;
                                      if (k == keyCode.up ||
                                          (k == keyCode.p  && e.ctrlKey == true)) { // up
                                          var p = a.removeClass('active').prev();
                                      (p.length ? p : item_menu.find('li:last')).addClass('active');
                                      } else if (k == keyCode.down ||
                                                 (k == keyCode.n  && e.ctrlKey == true)) { // down
                                          var n = a.removeClass('active').next();
                                      (n.length ? n : item_menu.find('li:first')).addClass('active');
                                      } else if (k == keyCode.enter) { // enter key to go to repo
                                          e.preventDefault();
                                          var url = actItem.attr('data-url');
                                          url = get_data(url);
                                          inputObj.val(url);
                                          setTimeout(hideAddItemMenu, 100);
                                          call_success();
                                      }
                                  } else {
                                      item_menu.find('li:first').addClass('active');
                                  }
                              }
                          } else {
                              var q = $(this).val();
                              (q != '') ? $.getJSON(
                                  reqUrl,
                                  {q:q},
                                  function (r) {
                                      item_menu.html($.tmpl(templ, r)).show();
                                  }) : showIntro();
                          }
                  }
                 );
        };
        return addItemMenu;
    });

/* @source  */;

require([
        'jquery',
        'mod/drop_down_list'
], function($, drop_down_list){
    var addProjectForm = $('#add-project-form');
    var success = function (data) {
        addProjectForm.submit();
    };

    // search for repos
    var reqUrl = '/api/autocomplete_repos';
    var templ = $('#templ-repos-autocomplete');

    $('#project_id').focusin(function(){
        var inputObj = $(this);
        drop_down_list(inputObj, success, 'dd', reqUrl, templ, "repos", '');
    });
});
