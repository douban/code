
require.config({ enable_ozma: true });


/* @source lib/tag-it.js */;

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

/* autogeneration */
define("tag-it", [], function(){});

/* @source lib/mousetrap.js */;

/**
 * Copyright 2012 Craig Campbell
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Mousetrap is a simple keyboard shortcut library for Javascript with
 * no external dependencies
 *
 * @version 1.2.2
 * @url craig.is/killing/mice
 */
(function() {

    /**
     * mapping of special keycodes to their corresponding keys
     *
     * everything in this dictionary cannot use keypress events
     * so it has to be here to map to the correct keycodes for
     * keyup/keydown events
     *
     * @type {Object}
     */
    var _MAP = {
            8: 'backspace',
            9: 'tab',
            13: 'enter',
            16: 'shift',
            17: 'ctrl',
            18: 'alt',
            20: 'capslock',
            27: 'esc',
            32: 'space',
            33: 'pageup',
            34: 'pagedown',
            35: 'end',
            36: 'home',
            37: 'left',
            38: 'up',
            39: 'right',
            40: 'down',
            45: 'ins',
            46: 'del',
            91: 'meta',
            93: 'meta',
            224: 'meta'
        },

        /**
         * mapping for special characters so they can support
         *
         * this dictionary is only used incase you want to bind a
         * keyup or keydown event to one of these keys
         *
         * @type {Object}
         */
        _KEYCODE_MAP = {
            106: '*',
            107: '+',
            109: '-',
            110: '.',
            111 : '/',
            186: ';',
            187: '=',
            188: ',',
            189: '-',
            190: '.',
            191: '/',
            192: '`',
            219: '[',
            220: '\\',
            221: ']',
            222: '\''
        },

        /**
         * this is a mapping of keys that require shift on a US keypad
         * back to the non shift equivelents
         *
         * this is so you can use keyup events with these keys
         *
         * note that this will only work reliably on US keyboards
         *
         * @type {Object}
         */
        _SHIFT_MAP = {
            '~': '`',
            '!': '1',
            '@': '2',
            '#': '3',
            '$': '4',
            '%': '5',
            '^': '6',
            '&': '7',
            '*': '8',
            '(': '9',
            ')': '0',
            '_': '-',
            '+': '=',
            ':': ';',
            '\"': '\'',
            '<': ',',
            '>': '.',
            '?': '/',
            '|': '\\'
        },

        /**
         * this is a list of special strings you can use to map
         * to modifier keys when you specify your keyboard shortcuts
         *
         * @type {Object}
         */
        _SPECIAL_ALIASES = {
            'option': 'alt',
            'command': 'meta',
            'return': 'enter',
            'escape': 'esc'
        },

        /**
         * variable to store the flipped version of _MAP from above
         * needed to check if we should use keypress or not when no action
         * is specified
         *
         * @type {Object|undefined}
         */
        _REVERSE_MAP,

        /**
         * a list of all the callbacks setup via Mousetrap.bind()
         *
         * @type {Object}
         */
        _callbacks = {},

        /**
         * direct map of string combinations to callbacks used for trigger()
         *
         * @type {Object}
         */
        _direct_map = {},

        /**
         * keeps track of what level each sequence is at since multiple
         * sequences can start out with the same sequence
         *
         * @type {Object}
         */
        _sequence_levels = {},

        /**
         * variable to store the setTimeout call
         *
         * @type {null|number}
         */
        _reset_timer,

        /**
         * temporary state where we will ignore the next keyup
         *
         * @type {boolean|string}
         */
        _ignore_next_keyup = false,

        /**
         * are we currently inside of a sequence?
         * type of action ("keyup" or "keydown" or "keypress") or false
         *
         * @type {boolean|string}
         */
        _sequence_type = false;

    /**
     * loop through the f keys, f1 to f19 and add them to the map
     * programatically
     */
    for (var i = 1; i < 20; ++i) {
        _MAP[111 + i] = 'f' + i;
    }

    /**
     * loop through to map numbers on the numeric keypad
     */
    for (i = 0; i <= 9; ++i) {
        _MAP[i + 96] = i;
    }

    /**
     * cross browser add event method
     *
     * @param {Element|HTMLDocument} object
     * @param {string} type
     * @param {Function} callback
     * @returns void
     */
    function _addEvent(object, type, callback) {
        if (object.addEventListener) {
            object.addEventListener(type, callback, false);
            return;
        }

        object.attachEvent('on' + type, callback);
    }

    /**
     * takes the event and returns the key character
     *
     * @param {Event} e
     * @return {string}
     */
    function _characterFromEvent(e) {

        // for keypress events we should return the character as is
        if (e.type == 'keypress') {
            return String.fromCharCode(e.which);
        }

        // for non keypress events the special maps are needed
        if (_MAP[e.which]) {
            return _MAP[e.which];
        }

        if (_KEYCODE_MAP[e.which]) {
            return _KEYCODE_MAP[e.which];
        }

        // if it is not in the special map
        return String.fromCharCode(e.which).toLowerCase();
    }

    /**
     * checks if two arrays are equal
     *
     * @param {Array} modifiers1
     * @param {Array} modifiers2
     * @returns {boolean}
     */
    function _modifiersMatch(modifiers1, modifiers2) {
        return modifiers1.sort().join(',') === modifiers2.sort().join(',');
    }

    /**
     * resets all sequence counters except for the ones passed in
     *
     * @param {Object} do_not_reset
     * @returns void
     */
    function _resetSequences(do_not_reset, max_level) {
        do_not_reset = do_not_reset || {};

        var active_sequences = false,
            key;

        for (key in _sequence_levels) {
            if (do_not_reset[key] && _sequence_levels[key] > max_level) {
                active_sequences = true;
                continue;
            }
            _sequence_levels[key] = 0;
        }

        if (!active_sequences) {
            _sequence_type = false;
        }
    }

    /**
     * finds all callbacks that match based on the keycode, modifiers,
     * and action
     *
     * @param {string} character
     * @param {Array} modifiers
     * @param {Event|Object} e
     * @param {boolean=} remove - should we remove any matches
     * @param {string=} combination
     * @returns {Array}
     */
    function _getMatches(character, modifiers, e, remove, combination) {
        var i,
            callback,
            matches = [],
            action = e.type;

        // if there are no events related to this keycode
        if (!_callbacks[character]) {
            return [];
        }

        // if a modifier key is coming up on its own we should allow it
        if (action == 'keyup' && _isModifier(character)) {
            modifiers = [character];
        }

        // loop through all callbacks for the key that was pressed
        // and see if any of them match
        for (i = 0; i < _callbacks[character].length; ++i) {
            callback = _callbacks[character][i];

            // if this is a sequence but it is not at the right level
            // then move onto the next match
            if (callback.seq && _sequence_levels[callback.seq] != callback.level) {
                continue;
            }

            // if the action we are looking for doesn't match the action we got
            // then we should keep going
            if (action != callback.action) {
                continue;
            }

            // if this is a keypress event and the meta key and control key
            // are not pressed that means that we need to only look at the
            // character, otherwise check the modifiers as well
            //
            // chrome will not fire a keypress if meta or control is down
            // safari will fire a keypress if meta or meta+shift is down
            // firefox will fire a keypress if meta or control is down
            if ((action == 'keypress' && !e.metaKey && !e.ctrlKey) || _modifiersMatch(modifiers, callback.modifiers)) {

                // remove is used so if you change your mind and call bind a
                // second time with a new function the first one is overwritten
                if (remove && callback.combo == combination) {
                    _callbacks[character].splice(i, 1);
                }

                matches.push(callback);
            }
        }

        return matches;
    }

    /**
     * takes a key event and figures out what the modifiers are
     *
     * @param {Event} e
     * @returns {Array}
     */
    function _eventModifiers(e) {
        var modifiers = [];

        if (e.shiftKey) {
            modifiers.push('shift');
        }

        if (e.altKey) {
            modifiers.push('alt');
        }

        if (e.ctrlKey) {
            modifiers.push('ctrl');
        }

        if (e.metaKey) {
            modifiers.push('meta');
        }

        return modifiers;
    }

    /**
     * actually calls the callback function
     *
     * if your callback function returns false this will use the jquery
     * convention - prevent default and stop propogation on the event
     *
     * @param {Function} callback
     * @param {Event} e
     * @returns void
     */
    function _fireCallback(callback, e, combo) {

        // if this event should not happen stop here
        if (Mousetrap.stopCallback(e, e.target || e.srcElement, combo)) {
            return;
        }

        if (callback(e, combo) === false) {
            if (e.preventDefault) {
                e.preventDefault();
            }

            if (e.stopPropagation) {
                e.stopPropagation();
            }

            e.returnValue = false;
            e.cancelBubble = true;
        }
    }

    /**
     * handles a character key event
     *
     * @param {string} character
     * @param {Event} e
     * @returns void
     */
    function _handleCharacter(character, e) {
        var callbacks = _getMatches(character, _eventModifiers(e), e),
            i,
            do_not_reset = {},
            max_level = 0,
            processed_sequence_callback = false;

        // loop through matching callbacks for this key event
        for (i = 0; i < callbacks.length; ++i) {

            // fire for all sequence callbacks
            // this is because if for example you have multiple sequences
            // bound such as "g i" and "g t" they both need to fire the
            // callback for matching g cause otherwise you can only ever
            // match the first one
            if (callbacks[i].seq) {
                processed_sequence_callback = true;

                // as we loop through keep track of the max
                // any sequence at a lower level will be discarded
                max_level = Math.max(max_level, callbacks[i].level);

                // keep a list of which sequences were matches for later
                do_not_reset[callbacks[i].seq] = 1;
                _fireCallback(callbacks[i].callback, e, callbacks[i].combo);
                continue;
            }

            // if there were no sequence matches but we are still here
            // that means this is a regular match so we should fire that
            if (!processed_sequence_callback && !_sequence_type) {
                _fireCallback(callbacks[i].callback, e, callbacks[i].combo);
            }
        }

        // if you are inside of a sequence and the key you are pressing
        // is not a modifier key then we should reset all sequences
        // that were not matched by this key event
        if (e.type == _sequence_type && !_isModifier(character)) {
            _resetSequences(do_not_reset, max_level);
        }
    }

    /**
     * handles a keydown event
     *
     * @param {Event} e
     * @returns void
     */
    function _handleKey(e) {

        // normalize e.which for key events
        // @see http://stackoverflow.com/questions/4285627/javascript-keycode-vs-charcode-utter-confusion
        if (typeof e.which !== 'number') {
            e.which = e.keyCode;
        }

        var character = _characterFromEvent(e);

        // no character found then stop
        if (!character) {
            return;
        }

        if (e.type == 'keyup' && _ignore_next_keyup == character) {
            _ignore_next_keyup = false;
            return;
        }

        _handleCharacter(character, e);
    }

    /**
     * determines if the keycode specified is a modifier key or not
     *
     * @param {string} key
     * @returns {boolean}
     */
    function _isModifier(key) {
        return key == 'shift' || key == 'ctrl' || key == 'alt' || key == 'meta';
    }

    /**
     * called to set a 1 second timeout on the specified sequence
     *
     * this is so after each key press in the sequence you have 1 second
     * to press the next key before you have to start over
     *
     * @returns void
     */
    function _resetSequenceTimer() {
        clearTimeout(_reset_timer);
        _reset_timer = setTimeout(_resetSequences, 1000);
    }

    /**
     * reverses the map lookup so that we can look for specific keys
     * to see what can and can't use keypress
     *
     * @return {Object}
     */
    function _getReverseMap() {
        if (!_REVERSE_MAP) {
            _REVERSE_MAP = {};
            for (var key in _MAP) {

                // pull out the numeric keypad from here cause keypress should
                // be able to detect the keys from the character
                if (key > 95 && key < 112) {
                    continue;
                }

                if (_MAP.hasOwnProperty(key)) {
                    _REVERSE_MAP[_MAP[key]] = key;
                }
            }
        }
        return _REVERSE_MAP;
    }

    /**
     * picks the best action based on the key combination
     *
     * @param {string} key - character for key
     * @param {Array} modifiers
     * @param {string=} action passed in
     */
    function _pickBestAction(key, modifiers, action) {

        // if no action was picked in we should try to pick the one
        // that we think would work best for this key
        if (!action) {
            action = _getReverseMap()[key] ? 'keydown' : 'keypress';
        }

        // modifier keys don't work as expected with keypress,
        // switch to keydown
        if (action == 'keypress' && modifiers.length) {
            action = 'keydown';
        }

        return action;
    }

    /**
     * binds a key sequence to an event
     *
     * @param {string} combo - combo specified in bind call
     * @param {Array} keys
     * @param {Function} callback
     * @param {string=} action
     * @returns void
     */
    function _bindSequence(combo, keys, callback, action) {

        // start off by adding a sequence level record for this combination
        // and setting the level to 0
        _sequence_levels[combo] = 0;

        // if there is no action pick the best one for the first key
        // in the sequence
        if (!action) {
            action = _pickBestAction(keys[0], []);
        }

        /**
         * callback to increase the sequence level for this sequence and reset
         * all other sequences that were active
         *
         * @param {Event} e
         * @returns void
         */
        var _increaseSequence = function(e) {
                _sequence_type = action;
                ++_sequence_levels[combo];
                _resetSequenceTimer();
            },

            /**
             * wraps the specified callback inside of another function in order
             * to reset all sequence counters as soon as this sequence is done
             *
             * @param {Event} e
             * @returns void
             */
            _callbackAndReset = function(e) {
                _fireCallback(callback, e, combo);

                // we should ignore the next key up if the action is key down
                // or keypress.  this is so if you finish a sequence and
                // release the key the final key will not trigger a keyup
                if (action !== 'keyup') {
                    _ignore_next_keyup = _characterFromEvent(e);
                }

                // weird race condition if a sequence ends with the key
                // another sequence begins with
                setTimeout(_resetSequences, 10);
            },
            i;

        // loop through keys one at a time and bind the appropriate callback
        // function.  for any key leading up to the final one it should
        // increase the sequence. after the final, it should reset all sequences
        for (i = 0; i < keys.length; ++i) {
            _bindSingle(keys[i], i < keys.length - 1 ? _increaseSequence : _callbackAndReset, action, combo, i);
        }
    }

    /**
     * binds a single keyboard combination
     *
     * @param {string} combination
     * @param {Function} callback
     * @param {string=} action
     * @param {string=} sequence_name - name of sequence if part of sequence
     * @param {number=} level - what part of the sequence the command is
     * @returns void
     */
    function _bindSingle(combination, callback, action, sequence_name, level) {

        // make sure multiple spaces in a row become a single space
        combination = combination.replace(/\s+/g, ' ');

        var sequence = combination.split(' '),
            i,
            key,
            keys,
            modifiers = [];

        // if this pattern is a sequence of keys then run through this method
        // to reprocess each pattern one key at a time
        if (sequence.length > 1) {
            _bindSequence(combination, sequence, callback, action);
            return;
        }

        // take the keys from this pattern and figure out what the actual
        // pattern is all about
        keys = combination === '+' ? ['+'] : combination.split('+');

        for (i = 0; i < keys.length; ++i) {
            key = keys[i];

            // normalize key names
            if (_SPECIAL_ALIASES[key]) {
                key = _SPECIAL_ALIASES[key];
            }

            // if this is not a keypress event then we should
            // be smart about using shift keys
            // this will only work for US keyboards however
            if (action && action != 'keypress' && _SHIFT_MAP[key]) {
                key = _SHIFT_MAP[key];
                modifiers.push('shift');
            }

            // if this key is a modifier then add it to the list of modifiers
            if (_isModifier(key)) {
                modifiers.push(key);
            }
        }

        // depending on what the key combination is
        // we will try to pick the best event for it
        action = _pickBestAction(key, modifiers, action);

        // make sure to initialize array if this is the first time
        // a callback is added for this key
        if (!_callbacks[key]) {
            _callbacks[key] = [];
        }

        // remove an existing match if there is one
        _getMatches(key, modifiers, {type: action}, !sequence_name, combination);

        // add this call back to the array
        // if it is a sequence put it at the beginning
        // if not put it at the end
        //
        // this is important because the way these are processed expects
        // the sequence ones to come first
        _callbacks[key][sequence_name ? 'unshift' : 'push']({
            callback: callback,
            modifiers: modifiers,
            action: action,
            seq: sequence_name,
            level: level,
            combo: combination
        });
    }

    /**
     * binds multiple combinations to the same callback
     *
     * @param {Array} combinations
     * @param {Function} callback
     * @param {string|undefined} action
     * @returns void
     */
    function _bindMultiple(combinations, callback, action) {
        for (var i = 0; i < combinations.length; ++i) {
            _bindSingle(combinations[i], callback, action);
        }
    }

    // start!
    _addEvent(document, 'keypress', _handleKey);
    _addEvent(document, 'keydown', _handleKey);
    _addEvent(document, 'keyup', _handleKey);

    var Mousetrap = {

        /**
         * binds an event to mousetrap
         *
         * can be a single key, a combination of keys separated with +,
         * an array of keys, or a sequence of keys separated by spaces
         *
         * be sure to list the modifier keys first to make sure that the
         * correct key ends up getting bound (the last key in the pattern)
         *
         * @param {string|Array} keys
         * @param {Function} callback
         * @param {string=} action - 'keypress', 'keydown', or 'keyup'
         * @returns void
         */
        bind: function(keys, callback, action) {
            _bindMultiple(keys instanceof Array ? keys : [keys], callback, action);
            _direct_map[keys + ':' + action] = callback;
            return this;
        },

        /**
         * unbinds an event to mousetrap
         *
         * the unbinding sets the callback function of the specified key combo
         * to an empty function and deletes the corresponding key in the
         * _direct_map dict.
         *
         * the keycombo+action has to be exactly the same as
         * it was defined in the bind method
         *
         * TODO: actually remove this from the _callbacks dictionary instead
         * of binding an empty function
         *
         * @param {string|Array} keys
         * @param {string} action
         * @returns void
         */
        unbind: function(keys, action) {
            if (_direct_map[keys + ':' + action]) {
                delete _direct_map[keys + ':' + action];
                this.bind(keys, function() {}, action);
            }
            return this;
        },

        /**
         * triggers an event that has already been bound
         *
         * @param {string} keys
         * @param {string=} action
         * @returns void
         */
        trigger: function(keys, action) {
            _direct_map[keys + ':' + action]();
            return this;
        },

        /**
         * resets the library back to its initial state.  this is useful
         * if you want to clear out the current keyboard shortcuts and bind
         * new ones - for example if you switch to another page
         *
         * @returns void
         */
        reset: function() {
            _callbacks = {};
            _direct_map = {};
            return this;
        },

       /**
        * should we stop this event before firing off callbacks
        *
        * @param {Event} e
        * @param {Element} element
        * @return {boolean}
        */
        stopCallback: function(e, element, combo) {

            // if the element has the class "mousetrap" then no need to stop
            if ((' ' + element.className + ' ').indexOf(' mousetrap ') > -1) {
                return false;
            }

            // stop for input, select, and textarea
            return element.tagName == 'INPUT' || element.tagName == 'SELECT' || element.tagName == 'TEXTAREA' || (element.contentEditable && element.contentEditable == 'true');
        }
    };

    // expose mousetrap to the global object
    window.Mousetrap = Mousetrap;

    // expose mousetrap as an AMD module
    if (typeof define === 'function' && define.amd) {
        define("mousetrap", Mousetrap);
    }
}) ();

/* @source mod/watch.js */;

define('mod/watch', [
  "jquery"
], function($){

  $(function() {
    var watch_btn = $("#watch-btn");
    var countLabel = $('#watched-count');
    var proj_id = watch_btn.attr("proj_id");

    var updateLabelBy = function (n) {
        var count = Number(countLabel.text()) || 0;
        if (count === 0 && n <= 0) { return; }

        count += n;
        countLabel.text(count.toString());
    };

    watch_btn.click(function() {

      if(watch_btn.hasClass('watch')) {
        $.post("/watch/"+proj_id, function(data) {
          if (!data.error) {
            watch_btn.text('Unwatch');
            watch_btn.addClass('unwatch');
            watch_btn.removeClass('watch');
            updateLabelBy(1);
          } else {
            // show error notification to user
            show_error("关注失败");
          }
        });
      }
      else{
        $.ajax("/watch/"+proj_id, {
          type: "DELETE",
          success: function(data) {
            if (!data.error) {
              watch_btn.text('Watch');
              watch_btn.addClass('watch');
              watch_btn.removeClass('unwatch');
              updateLabelBy(-1);
            } else {
              show_error("取消关注失败");
            }
          },
          error: function(e) {
            show_error("取消关注失败");
          }
        });
      }
    });

    function show_success(msg) {
        var successDiv = $(".navbar .success");
        if (successDiv.size() === 0 ) {
            successDiv= $("<div>").addClass("success").addClass("alert-success");
            $("div.navbar").append(successDiv);
        }
        successDiv.html(msg);
        successDiv.fadeOut(1500, function () {
            $(this).remove();
        });
    }

    function show_error(msg) {
        var errorDiv = $(".navbar .error");
        if (errorDiv.size() === 0 ) {
            errorDiv = $("<div>").addClass("error").addClass("alert-error");
            $("div.navbar").append(errorDiv);
        }
        errorDiv.html(msg);
    }

  });
});

/* @source lib/zen-form.js */;

/** Zen Forms 1.0.0 | MIT License | git.io/zen-form */

(function($) {

    $.fn.zenForm = function(settings) {

        settings = $.extend({
            trigger: '.go-zen',
            theme: 'dark'
        }, settings);

        /**
         * Helper functions
         */
        var Utils = {

            watchEmpty: function($form) {

                $form.find('input, textarea').each(function() {
                   $(this).on('change', function() {
                        $(this)[ $(this).val() ? 'removeClass' : 'addClass' ]('empty');
                   }).trigger('change');
                });

            }

        }, // Utils

        /**
         * Core functionality
         */
        App = {

            /**
             * Wrapper element
             */
            Environment: null,

            /**
             * Functions to create and manipulate environment
             */
            env: {

                create: function() {

                    var theme = settings.theme == 'dark' ? '' : ' light-theme';

                    return $('<div>', {class: 'zen-forms' + theme}).hide().appendTo('body').fadeIn(200);

                }, // create

                /**
                 * Update orginal inputs with new values and destroy Environment
                 */
                destroy: function($elements) {

                    // Update orginal inputs with new values
                    $elements.each(function(i) {

                        var $el = $('#zen-forms-input' + i);

                        if ( $el.length )
                            $(this).val($el.val());

                    }).filter('input:text,textarea').eq(0).focus();

                    $('.zen-forms').fadeOut(200, function() {
                        $(this).remove();
                    });

                }, // destroy

                /**
                 * Append inputs, textareas to Environment
                 */
                add: function($elements) {

                    $elements.each(function(i) {

                        var $this    = $(this),
                            $wrapper = App.env.addObject(App.Environment, 'div', {class: 'zen-forms-input-wrap'}),

                            value = $this.val(),
                            id    = $this.attr('id'),
                            ID    = 'zen-forms-input' + i,
                            label = $("label[for=" + id + "]").text() || $this.attr('placeholder') || '';

                        // Exclude specified elements
                        if ( $.inArray( $this.attr('type'), ['checkbox', 'radio', 'submit']) == -1) {

                            if ( $this.is('input') )
                                App.env.addObject($wrapper, 'input', {
                                    id: ID,
                                    value: value,
                                    type: $this.attr('type')
                                });
                            else
                                App.env.addObject($wrapper, 'textarea', {
                                    id: ID,
                                    text: value
                                });

                            App.env.addObject($wrapper, 'label', {
                                for: ID,
                                text: label
                            });

                        }

                    });

                }, // add

                /**
                 * Wrapper for creating jQuery objects
                 */
                addObject: function($wrapper, type, params, fn, fnMethod) {

                    return $('<'+type+'>', params).on(fnMethod || 'click', fn).appendTo($wrapper);

                }, // addObject

                switchTheme: function() {

                    App.Environment.toggleClass('light-theme');

                } // switchTheme

            }, // env

            zen: function($elements) {

                // Create environment
                App.Environment = App.env.create();

                // Add close button
                App.env.addObject(App.Environment, 'a', {
                    class: 'zen-forms-close-button',
                    html: '&times;'
                }, function() {
                    App.env.destroy($elements);
                });

                // Add theme switch button
                App.env.addObject(App.Environment, 'a', {
                    class: 'zen-forms-theme-switch',
                    html: '&bull;'
                }, function() {
                    App.env.switchTheme();
                });

                // Add inputs and textareas from form
                App.env.add($elements);

                App.Environment.keydown(function(e) {
                  // Esc close
                  if (e.which == 27) {
                    App.env.destroy($elements);
                  }
                }).find('input:text, textarea').eq(0).focus();

                // Watch inputs and add "empty" class if needed
                Utils.watchEmpty(App.Environment);

            }, // zen

        }; // App

        return this.each(function() {

            var $this = $(this);

            function zen() {
                App.zen( $this.is('form') ? $this.find('input, textarea') : $this );
            }

            if (!settings.trigger) return zen();

            $(settings.trigger).on('click', function(event) {
                event.preventDefault();
                zen();
            });

        });

    };

})(jQuery);

/* autogeneration */
define("lib/zen-form", [], function(){});

/* @source lib/store.js */;

;(function(win){
	var store = {},
		doc = win.document,
		localStorageName = 'localStorage',
		namespace = '__storejs__',
		storage

	store.disabled = false
	store.set = function(key, value) {}
	store.get = function(key) {}
	store.remove = function(key) {}
	store.clear = function() {}
	store.transact = function(key, defaultVal, transactionFn) {
		var val = store.get(key)
		if (transactionFn == null) {
			transactionFn = defaultVal
			defaultVal = null
		}
		if (typeof val == 'undefined') { val = defaultVal || {} }
		transactionFn(val)
		store.set(key, val)
	}
	store.getAll = function() {}

	store.serialize = function(value) {
		return JSON.stringify(value)
	}
	store.deserialize = function(value) {
		if (typeof value != 'string') { return undefined }
		try { return JSON.parse(value) }
		catch(e) { return value || undefined }
	}

	// Functions to encapsulate questionable FireFox 3.6.13 behavior
	// when about.config::dom.storage.enabled === false
	// See https://github.com/marcuswestin/store.js/issues#issue/13
	function isLocalStorageNameSupported() {
		try { return (localStorageName in win && win[localStorageName]) }
		catch(err) { return false }
	}

	if (isLocalStorageNameSupported()) {
		storage = win[localStorageName]
		store.set = function(key, val) {
			if (val === undefined) { return store.remove(key) }
			storage.setItem(key, store.serialize(val))
			return val
		}
		store.get = function(key) { return store.deserialize(storage.getItem(key)) }
		store.remove = function(key) { storage.removeItem(key) }
		store.clear = function() { storage.clear() }
		store.getAll = function() {
			var ret = {}
			for (var i=0; i<storage.length; ++i) {
				var key = storage.key(i)
				ret[key] = store.get(key)
			}
			return ret
		}
	} else if (doc.documentElement.addBehavior) {
		var storageOwner,
			storageContainer
		// Since #userData storage applies only to specific paths, we need to
		// somehow link our data to a specific path.  We choose /favicon.ico
		// as a pretty safe option, since all browsers already make a request to
		// this URL anyway and being a 404 will not hurt us here.  We wrap an
		// iframe pointing to the favicon in an ActiveXObject(htmlfile) object
		// (see: http://msdn.microsoft.com/en-us/library/aa752574(v=VS.85).aspx)
		// since the iframe access rules appear to allow direct access and
		// manipulation of the document element, even for a 404 page.  This
		// document can be used instead of the current document (which would
		// have been limited to the current path) to perform #userData storage.
		try {
			storageContainer = new ActiveXObject('htmlfile')
			storageContainer.open()
			storageContainer.write('<s' + 'cript>document.w=window</s' + 'cript><iframe src="/favicon.ico"></iframe>')
			storageContainer.close()
			storageOwner = storageContainer.w.frames[0].document
			storage = storageOwner.createElement('div')
		} catch(e) {
			// somehow ActiveXObject instantiation failed (perhaps some special
			// security settings or otherwse), fall back to per-path storage
			storage = doc.createElement('div')
			storageOwner = doc.body
		}
		function withIEStorage(storeFunction) {
			return function() {
				var args = Array.prototype.slice.call(arguments, 0)
				args.unshift(storage)
				// See http://msdn.microsoft.com/en-us/library/ms531081(v=VS.85).aspx
				// and http://msdn.microsoft.com/en-us/library/ms531424(v=VS.85).aspx
				storageOwner.appendChild(storage)
				storage.addBehavior('#default#userData')
				storage.load(localStorageName)
				var result = storeFunction.apply(store, args)
				storageOwner.removeChild(storage)
				return result
			}
		}

		// In IE7, keys may not contain special chars. See all of https://github.com/marcuswestin/store.js/issues/40
		var forbiddenCharsRegex = new RegExp("[!\"#$%&'()*+,/\\\\:;<=>?@[\\]^`{|}~]", "g")
		function ieKeyFix(key) {
			return key.replace(forbiddenCharsRegex, '___')
		}
		store.set = withIEStorage(function(storage, key, val) {
			key = ieKeyFix(key)
			if (val === undefined) { return store.remove(key) }
			storage.setAttribute(key, store.serialize(val))
			storage.save(localStorageName)
			return val
		})
		store.get = withIEStorage(function(storage, key) {
			key = ieKeyFix(key)
			return store.deserialize(storage.getAttribute(key))
		})
		store.remove = withIEStorage(function(storage, key) {
			key = ieKeyFix(key)
			storage.removeAttribute(key)
			storage.save(localStorageName)
		})
		store.clear = withIEStorage(function(storage) {
			var attributes = storage.XMLDocument.documentElement.attributes
			storage.load(localStorageName)
			for (var i=0, attr; attr=attributes[i]; i++) {
				storage.removeAttribute(attr.name)
			}
			storage.save(localStorageName)
		})
		store.getAll = withIEStorage(function(storage) {
			var attributes = storage.XMLDocument.documentElement.attributes
			var ret = {}
			for (var i=0, attr; attr=attributes[i]; ++i) {
				var key = ieKeyFix(attr.name)
				ret[attr.name] = store.deserialize(storage.getAttribute(key))
			}
			return ret
		})
	}

	try {
		store.set(namespace, namespace)
		if (store.get(namespace) != namespace) { store.disabled = true }
		store.remove(namespace)
	} catch(e) {
		store.disabled = true
	}
	store.enabled = !store.disabled
	if (typeof module != 'undefined' && module.exports) { module.exports = store }
	else if (typeof define === 'function' && define.amd) { define("store", store) }
	else { win.store = store }
})(this.window || global);

/* @source mod/user_following.js */;

define('store', 'lib/store.js');
define('mod/user_following', [
  "jquery",
  "store"
], function($, store) {
  var API_USER_FOLLOWING_PATH = "/api/user/following"
  var USER_FOLLOWING_KEY = "user-following";
  var USER_FOLLOWING_UPDATE_KEY= "date:user-following"
  var ONE_DAY_IN_SECONDS = 60*60*24;

  var update = function() {
    var currentTime = new Date().getTime();
    var lastTime = store.get(USER_FOLLOWING_UPDATE_KEY);
    if (lastTime && (currentTime - lastTime) < ONE_DAY_IN_SECONDS ) {
      return;
    }

    $.ajax(
      API_USER_FOLLOWING_PATH
    ).done(function(users){
      var following = $.map(users, function(item){
        return item["username"];
      });
      store.set(USER_FOLLOWING_KEY, following);
      store.set(USER_FOLLOWING_UPDATE_KEY, currentTime);
    }).fail(function(jqxhr, textStatus, error){
      return;
    });
  }

  return {
    update: update,
    val: function(){
      return store.get(USER_FOLLOWING_KEY) || [];
    }
  };

});

/* @source mod/input-ext.js */;

define('mousetrap', 'lib/mousetrap.js');

define("mod/input-ext", 
    [
  "jquery",
  "mod/user_following",
  "jquery-caret",
  "jquery-atwho",
  "mousetrap",
  "lib/zen-form"
],
    function ($, userFollowing) {
        var inputExt = {};
        var emojis = [
            'airplane', 'alien', 'art', 'bear', 'beer', 'bike', 'bomb', 'book',
            'bulb', 'bus', 'cake', 'calling', 'clap', 'cocktail', 'code', 'computer',
            'cool', 'cop', 'email', 'feet', 'fire', 'fish', 'fist', 'gift', 'hammer',
            'heart', 'iphone', 'key', 'leaves', 'lgtm', 'lipstick', 'lock', 'mag', 'mega',
            'memo', 'moneybag', 'new', 'octocat', 'ok', 'palm_tree', 'pencil', 'punch',
            'runner', 'scissors', 'ship', 'shipit', 'ski', 'smile', 'smoking', 'sparkles',
            'star', 'sunny', 'taxi', 'thumbsdown', 'thumbsup', 'tm', 'tophat', 'train',
            'trollface', 'v', 'vs', 'warning', 'wheelchair', 'zap', 'zzz', 'see_no_evil',
            'hear_no_evil', 'speak_no_evil', 'monkey', 'monkey_face', 'manybeers', 'beers',
            'hhkb', 'ruby'
        ], emoji_list = $.map(emojis, function(value, i) {return {key: value + ':', name:value};});
        inputExt.enableEmojiInput = function (el) {
            el.atwho('(?:^|\\s):',
                     {data:emoji_list, limit:7,
                         tpl:'<li data-value="${key}">${name} <img src="/static/emoji/${name}.png" height="20" width="20" /></li>'});
                         return el;
        };

        inputExt.enableAutoCompleteFollowingAndTeam = function (el) {
            var teams = JSON.parse($('#all-teams').val() || '[]');
            var users = teams.concat(userFollowing.val());

            $(el).atwho("@", {
                data: users,
                limit: 7
            });
        };

        // 输入#自动提示pr信息
        inputExt.enablePullsInput = function (el) {
            var projectName = el.attr('data-project-name');
            if (!projectName) return el;
            $.getJSON('/' + projectName + '/pulls/all_data', function (r) {
                var pulls = $.map(
                    r, function(value, i) {
                    return {key: value.id, name:value.id + ' ' + value.title, title:value.title};
                });
                el.atwho('(?:^|\\s)#',
                         {data:pulls, limit:7,
                             tpl:'<li data-value="${key}"><small>#${key}</small> ${title}</li>'});
            });
            return el;
        };

        inputExt.shortcut2submit = function (el) {
            Mousetrap.bind(
                ['command+enter', 'ctrl+enter'],
                function (e) {
                    if (el && (e.srcElement || e.target) == $(el)[0] && !$(el).closest('form').hasClass('submitting')) {
                        e.preventDefault ? e.preventDefault() : (e.returnValue = false);
                        $(el).closest('form').addClass('submitting').submit();
                    }
                },
                'keydown'
            );
        };

        // 进入全屏模式
        inputExt.enableZenMode = function (el) {
            var trigger = '.go-zen';
            el = $(el);
            el.zenForm({trigger:trigger, theme:'light'}).dblclick(function(e) {
                if (!e.altKey) return;
                $(this).zenForm({ trigger: null, theme: 'light' });
                fix();
            });

            $(trigger).click(fix);

            function fix() {
                var textarea = $('.zen-forms-input-wrap textarea');
                if (textarea) {
                    inputExt.enableEmojiInput(textarea);
                    textarea.attr({
                        'data-project-name': el.attr('data-project-name'),
                        'placeholder': el.attr('placeholder')
                    });

                    inputExt.enablePullsInput(textarea);

                    var participants = $('#participants').val();
                    if (participants) {
                        participants = JSON.parse(participants);
                        textarea.atwho("@", {data:participants, limit:7});
                    }

                    // 因为zen-form设置的z-index非常高(99999)所以将at-view调更高
                    $('#at-view').css('z-index', 100000);
                }
            }
        };

        var focusToEnd = function(els) {
            return $(els).each(function() {
                var v = $(this).val();
                $(this).focus().val("").val(v);
            });
        };

        inputExt.enableQuickQuotes = function (el) {
            Mousetrap.bind(
                ['r'],
                function (e) {
                    var oldVal = $(el).val(), newVal, selVal = window.getSelection().toString();
                    selVal = '> ' + selVal.split('\n').join('\n> ');
                    newVal = oldVal.concat((oldVal != '') ? '\n\n':'', selVal, '\n\n');
                    $("html, body").animate({scrollTop: $(document).height()}, "slow");
                    $(el).val(newVal);
                    focusToEnd(el);
                },
                'keyup'
            );
        };

        inputExt.enableFileUpload = function (uploader, textarea, is_image) {
            uploader.submit(
                function() {
                $(this).ajaxSubmit({
                    dataType: 'json',
                    type: 'POST',
                    delegation: true,
                    success: function(r) {
                        var oldText = textarea.val(),
                        newText = oldText +
                            (oldText.length == 0 ? '' : '\n') +
                            (is_image? '!' : '') +
                            '[' + r.origin_filename + '](' + r.url + ')';
                        textarea.val(newText);
                    },
                    error: function(r) {
                        alert("上传错误，请确认您上传的文件类型合法");
                    }
                });
                return false;
            });

            uploader.find('input').change(function () {
                uploader.submit();
            });
        };

        inputExt.enableImageUpload = function (uploader, textarea) {
            inputExt.enableFileUpload(uploader,textarea, true);
        };

        inputExt.enableUpload = function(upload_widget,textarea){
            inputExt.enableImageUpload(upload_widget.find(".upload-image-form"),textarea);
            inputExt.enableFileUpload(upload_widget.find(".upload-file-form"),textarea);
        };

        return inputExt;
    }
);

/* @source  */;

define('mousetrap', 'lib/mousetrap.js');
define('tag-it', 'lib/tag-it.js');

require(
    ['jquery'
     , 'mod/input-ext'
     , 'jquery-caret'
     , 'jquery-atwho'
     , 'jquery-timeago'
     , 'bootstrap'
     , 'mod/watch'
     , 'mousetrap'
     , 'tag-it'],
    function($, inputExt){
        $(function () {
            inputExt.enableZenMode('#pull_body');
            inputExt.enableAutoCompleteFollowingAndTeam('#pull_body');
            //previewable-comment-form
            $('.previewable-comment-form .js-preview-tabs a.preview-tab').on('show', function(e) {
                $('#preview_bucket p').html("Loading preview...");
            }).on('shown', function(e) {
                var url = $('#preview_bucket .content-body').data('api-url');
                var text = $('#write_bucket textarea').val();
                $('#preview_bucket .content-body').load(url, {text: text});
            });

            $('.new-issue form').submit(
                function () {
                    $(this).find('button[type="submit"]').attr('disabled', true).addClass('disabled');
                    //Google Analytic Events
                    ga('send', 'event', 'issue', 'create');
                }
            );

              var uploader = $('#form-file-upload'),
              textarea = $('#write_bucket textarea');
              inputExt.enableUpload(uploader, textarea);

              $('#issue-tags').tagit({input_name: 'issue_tags', tag_list: $('.label')});

          });
    });
