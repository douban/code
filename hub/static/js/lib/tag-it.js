(function($) {

    $.fn.tagit = function(options) {

        var el = this;

        const BACKSPACE = 8;
        const ENTER = 13;
        const SPACE = 32;
        const COMMA = 44;

        // add the tagit CSS class.
        el.addClass("tagit");

        // create the input field.
        var html_input_field = "<li class=\"tagit-new\"><input class=\"tagit-input\" type=\"text\" /></li>\n";
        el.html (html_input_field);

        tag_input = el.children(".tagit-new").children(".tagit-input");

        $(this).click(function(e){
            if (e.target.tagName == 'A') {
                // Removes a tag when the little 'x' is clicked.
                // Event is binded to the UL, otherwise a new tag (LI > A) wouldn't have this event attached to it.
                $(e.target).parent().remove();
            }
            else {
                // Sets the focus() to the input field, if the user clicks anywhere inside the UL.
                // This is needed because the input field needs to be of a small size.
                tag_input.focus();
            }
        });

        $(this).delegate('.tagit-choice', 'click', function(){
            // the little 'x' is hard to click =.=
            $(this).remove();
        });

        tag_input.blur(function () {
            var unhandlerTag = tag_input.val();
            unhandlerTag = unhandlerTag.replace(/,+$/,"");
            unhandlerTag = unhandlerTag.trim();
            if (unhandlerTag !== ''){
                if (is_new (unhandlerTag)) {
                    create_choice (unhandlerTag);
                }
                // Cleaning the input.
                tag_input.val("");
            }
        });

        if (options) {
            if (options.hasOwnProperty('tag_list')) {
                options.tag_list.click(function(event){

                    var typed = $(event.target).html();
                    typed = typed.replace(/,+$/,"");
                    typed = typed.trim();

                    if (typed != "") {
                        if (is_new (typed)) {
                            create_choice (typed);
                        }
                    }
                });
            }
            if (options.hasOwnProperty('fillup')) {
                for (var i in options.fillup) {
                    create_choice(options.fillup[i]);
                }
            }
        }
        tag_input.keypress(function(event){
            if (event.which == BACKSPACE) {
                if (tag_input.val() == "") {
                    // When backspace is pressed, the last tag is deleted.
                    $(el).children(".tagit-choice:last").remove();
                }
            }
            // Comma/Space/Enter are all valid delimiters for new tags.
            else if (event.which == COMMA || event.which == SPACE || event.which == ENTER) {
                event.preventDefault();

                var typed = tag_input.val();
                typed = typed.replace(/,+$/,"");
                typed = typed.trim();

                if (typed != "") {
                    if (is_new (typed)) {
                        create_choice (typed);
                    }
                    // Cleaning the input.
                    tag_input.val("");
                }
            }
        });

        function is_new (value){
            var is_new = true;
            this.tag_input.parents("ul").children(".tagit-choice").each(function(i){
                n = $(this).children("input").val();
                if (value == n) {
                    is_new = false;
                }
            });
            return is_new;
        }
        function create_choice (value){
            var el = "";
            el  = "<li class=\"tagit-choice\">\n";
            el += value + "\n";
            el += "<a class=\"tag-close\">x</a>\n";
            el += "<input type=\"hidden\" style=\"display:none;\" value=\""+value+"\" name=\""+ options.input_name +"\">\n";
            el += "</li>\n";
            var li_search_tags = this.tag_input.parent();
            $(el).insertBefore (li_search_tags);
            this.tag_input.val("");
        }
    };

    String.prototype.trim = function() {
        return this.replace(/^\s+|\s+$/g,"");
    };

})(jQuery);
