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
