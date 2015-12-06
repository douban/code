define(['jquery', ],
        function ($) {
            var follow = {};
            follow.button = function(btn){
                $(btn).click(function(){
                    var $btn = $(this);
                    var link = $btn.attr('href');
                    var $followersCount = $('.followers-count');
                    var currentCount = parseInt($followersCount.text(), '10');

                    $.ajax($btn.attr('href'),
                        {
                            type: 'POST',
                            dataType:'json',
                            success:function(res){
                                if(res.action>0){
                                    $followersCount.text(currentCount+1);
                                    $btn.addClass('btn-danger follow');
                                    $btn.removeClass('btn-success unfollow');
                                    $btn.find('span').text("Unfollow");
                                    $btn.attr(
                                      'href',
                                      link.replace(/follow$/,"unfollow")
                                    )
                                }
                                else if(res.action<0){
                                    $followersCount.text(currentCount-1);
                                    $btn.addClass('btn-success unfollow');
                                    $btn.removeClass('btn-danger follow');
                                    $btn.find('span').text("Follow");
                                    $btn.attr(
                                      'href',
                                      link.replace(/unfollow$/,"follow")
                                    )
                                }
                                else{
                                    if(res.msg) {
                                      alert(res.msg);
                                    } else {
                                      alert("please try again later:(");
                                    }

                                    return;
                                }
                            },
                        });
                return false;
                });
            }
            return follow;
        });
