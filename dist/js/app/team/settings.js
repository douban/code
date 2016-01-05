
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

require.config({ enable_ozma: true });
require(['jquery', 'bootbox', 'mod/drop_down_list'],
        function($, bootbox, drop_down_list){
            $(function () {
                var post_data = function (field_id) {
                        var fieldObj = $(field_id),
                            user_id = fieldObj.find('.input_user_id').val(),
                            team_uid = fieldObj.find('.input_user_id').attr('team_uid'),
                            identity = fieldObj.find('.input_identity').val();
                        if (user_id === ''){
                            var msg = 'uid不能为空';
                            show_error(fieldObj, msg);
                            return false;
                        }else{
                            $.ajax({
                                url: '/hub/team/' + team_uid + '/add_user',
                                type: 'POST',
                                data: {'user_id': user_id, 'identity': identity},
                                dataType: 'json',
                                success: function (msg) {
                                    if (msg.r === 0){
                                        var user_id = msg.uid,
                                            avatar_url = msg.avatar_url,
                                            new_user = '<li><img height="20" src="'+avatar_url+'" width="20"><a href="/people/'+user_id+'/">'+user_id+'</a><a href="Javascript:void(0);" user_id="'+user_id+'" team_uid="'+team_uid+'" class="remove-user remove action">(remove)</a></li>';
                                        fieldObj.find('.usernames').find('li:last').parent().append(new_user);
                                        fieldObj.find('.alert-error').remove();
                                    } else {
                                        var error = msg.error;
                                            show_error(fieldObj, error);
                                    }
                                }
                            });
                        }
                    },
                    reqUrl = '/api/autocomplete_users',
                    templ = $('#templ-users-autocomplete');

                $('.add_team_member_btn').live('click', function () {
                    var btnObj = $(this),
                        field_id = btnObj.parent().parent().attr('id');
                        post_data('#'+field_id);
                        $('#'+field_id).find('.add-item-menu').remove();
                });

                $('.input_user_id').one('focusin', function (){
                    var inputObj = $(this),
                        field_id = inputObj.parent().parent().attr('id'),
                        form_id = inputObj.parent().attr('id');
                        $('#'+field_id).find('.add-item-menu').remove();
                        $('#'+field_id).find('.alert-error').remove();
                        drop_down_list(inputObj, post_data, '#'+form_id, reqUrl, templ, "users", '#'+field_id);
                        $('#'+field_id).find('.add-item-menu').remove();
                });

                $('.remove-user').live('click', function(event){
                    var removeBtn = $(this),
                        field_id = removeBtn.parent().parent().parent().attr('id'),
                        user_id = removeBtn.attr('user_id'),
                        team_uid = removeBtn.attr('team_uid'),
                        fieldObj = $('#'+field_id);
                        $('#'+field_id).find('.alert-error').remove();

                        $.ajax({
                            url: '/hub/team/' + team_uid + '/remove_user',
                            type: 'POST',
                            data: {'user_id': user_id},
                            dataType: 'json',
                            success: function (msg) {
                                if (msg.r === 0){
                                   $('.remove-user[user_id='+user_id+']').parent().remove();
                                } else {
                                    var error = msg.error;
                                        show_error(fieldObj, error);
                                }
                            }
                        });
                });

                var delete_team_btn = $('#settings_del_team');
                delete_team_btn.click(function () {
                    var team_id = $(this).attr('data-team');
                    bootbox.confirm("Are you sure?", function(confirmed){
                        if (confirmed) {
                            $.ajax({
                                url: '/hub/team/' + team_id + '/remove',
                                type: 'POST',
                                data: {},
                                dataType: 'json',
                                success: function (msg) {
                                    if (msg.r === 0){
                                        location.href = '/hub/teams';
                                    }
                                }
                            });
                        }
                    });
                });

                function show_error(targetObj, msg) {
                    var html = '<p class="alert alert-error">'+msg+'</p>';
                    targetObj.find('.alert-error').remove();
                    targetObj.append(html);
                }
        });
    $('#doc_project').on('change', function() {
        var select = $(this);
        var team_name = select.data('team-uid');
        $.ajax({
            type: 'POST',
            data: JSON.stringify({
                'content': select.val()
            }),
            contentType: 'application/json; charset=UTF-8',
            url: '/api/teams/' + team_name + '/doc_project/',
            dataType: 'json',
            success: function (ret) {
                if (ret.status == 201) {
                    select.find('option:selected').removeAttr('selected');
                    select.find('option[value="' + ret.content + '"]').attr("selected",true);
                }
            }
        });
    });

    var enableImageUpload = function (uploader){
            uploader.submit(
                function() {
                $(this).ajaxSubmit({
                    dataType: 'json',
                    delegation: true,
                    success: function(r){
                        var team_id = uploader.data('team-uid');
                        var url = "/teams/" + team_id + "/upload_profile";
                        $.post(url,r,function(ret){
                                if (ret.r == 0){
                                var img = document.getElementById("profile_url");
                                img.src = r.url;
                                }
                            }, 'json');
                  },
                    error: function(r) {
                        alert("上传错误，请确认您上传的文件类型合法");
                    }
                });
                return false;
        });
        };
    var uploader = $('#form-file-upload');
    enableImageUpload(uploader);
});
