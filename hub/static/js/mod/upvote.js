define(['jquery', ],
        function ($) {
            var upvote = {};
            upvote.button = function(btn){
                $(btn).click(function(){
                    var method = 'PUT';
                    var $ts = $(this);
                    if($ts.hasClass("upvoted")) method = 'DELETE';

                    $.ajax("upvote",
                        {
                            type:method,
                            dataType:'json',
                            success:function(res){
                                console.log(res);
                                if(res.action>0){
                                    console.log($ts);
                                    $ts.addClass('btn-danger upvoted');
                                    $ts.find('i').removeClass('icon-chevron-up').addClass('icon-chevron-down');
                                    $ts.find('span').text("Unvote");
                                }
                                else if(res.action<0){
                                    $ts.removeClass('btn-danger upvoted');
                                    $ts.find('i').removeClass('icon-chevron-down').addClass('icon-chevron-up');
                                    $ts.find('span').text("Vote");
                                }
                                else{
                                    alert(res.msg);
                                    return;
                                }
                                $('#vote-count').text(res.count);
                            },
                        });
                return false;
                });

            }
            return upvote;
        });
