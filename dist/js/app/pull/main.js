
require.config({ enable_ozma: true });


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

/* @source mod/pull_key.js */;

define("mod/pull_key", [
  "jquery",
  "mousetrap"
], function ($, mousetrap)  {
    var keywrap = function (e, action) {
        if (e.srcElement && e.srcElement.tagName == 'BODY') {
            e.preventDefault ? e.preventDefault() : (e.returnValue = false);
            action(e);
        }
    }
    Mousetrap.bind(
        'g g',
        function (e) {
            keywrap(e, function (e) {
                $("html, body").animate({scrollTop: 0});
            });
        }
    );
    Mousetrap.bind(
        'g d',
        function (e) {
            keywrap(e, function (e) {
                var tab = $('.pull-nav a[href="#discussion-pane"]');
                if (tab && !tab.parent().hasClass('active')) {
                    $("html, body").animate({scrollTop: 0});
                    tab.click();
                }
            });
        }
    );
    Mousetrap.bind(
        'g c',
        function (e) {
            keywrap(e, function (e) {
                var tab = $('.pull-nav a[href="#commits-pane"]');
                if (tab && !tab.parent().hasClass('active')) {
                    $("html, body").animate({scrollTop: 0});
                    tab.click();
                }
            });
        }
    );
    Mousetrap.bind(
        'g f',
        function (e) {
            keywrap(e, function (e) {
                var tab = $('.pull-nav a[href="#files-pane"]');
                if (tab && !tab.parent().hasClass('active')) {
                    $("html, body").animate({scrollTop: 0});
                    tab.click();
                }
            });
        }
    );
})

/* @source mod/mute.js */;

define("mod/mute", [
  "jquery"
],
        function ($) {
            var mute_buttons = $('.mute-buttons');
            mute_buttons.find('a').click(function(){
                var href = $(this).attr("href");
                $.getJSON(href, 
                    function(data){
                        var status = data["status"];
                        if(status=='on'){
                            mute_buttons.find('.mute-on').addClass('btn-success');
                            mute_buttons.find('.mute-off').removeClass('btn-warning');
                        }else{
                            mute_buttons.find('.mute-on').removeClass('btn-success');
                            mute_buttons.find('.mute-off').addClass('btn-warning');
                        }
                    });
                return false;
            })
        });

/* @source mod/tasklist.js */;

define('mod/tasklist', [
  "jquery",
  "jquery-lazyload"
], function($, _) {
  $(function() {
        $('body').delegate(
            '.tasklist-enabled input[type=checkbox]', 'click', function(){
                var editForm = $(this).parents('.tasklist-enabled').find('.tasklist-form');
                if (editForm && editForm.length) {
                    var el = editForm.find('#issue_body'), content = el.val(),
                    p = /- \[[x\s]\]/g, joints = content.match(p), parts = content.split(p),
                    idx = Number($(this).data('item-index'));
                    joints[idx] = joints[idx] == '- [x]' ? '- [ ]' : '- [x]', content = '';
                    for (var i=0, len=parts.length; i<len; i++) {
                        parts[i] && (content = content.concat(parts[i]));
                        joints[i] && (content = content.concat(joints[i]));
                    }
                    el.val(content);
                    editForm.submit();
                }
            });
  });
});

/* @source mod/user_profile_card.js */;

define('mod/user_profile_card', [
  "jquery",
  "jquery-tmpl"
], function($) {
    $(function () {
        var userCard, teamCard, users = {}, user_type = {};
        $(document).delegate(
            '.user-link,.user-mention', 'mouseover',
            function (e) {
                if (!userCard) {
                    userCard = $('<div class="user-card"></div>').appendTo('body')
                        .mouseleave(function () {
                            $(this).hide();
                            $('.team-card').hide();
                        });
                }
                if (!teamCard) {
                    teamCard = $('<div class="team-card"></div>').appendTo('body')
                        .mouseleave(function () {
                            $(this).hide();
                            $('.user-card').hide();
                        });
                }
                var pos = $(this).offset();
                pos.left = pos.left - 5;
                pos.top = pos.top - 5;
                var name = /@?(\w+)/.exec($(this).text())[1], user = users[name];

                if (!user) {
                    $.getJSON('/api/card_info', {user: name},
                              function (r) {
                                  if (r.team) {
                                      teamCard.css(pos).empty().show();
                                      teamCard.append($.tmpl($('#templ-team-card'), r.team));
                                      user_type[name] = 'team';
                                      users[name] = r.team;
                                  } else {
                                      userCard.css(pos).empty().show();
                                      userCard.append($.tmpl($('#templ-user-card'), r.user));
                                      user_type[name] = 'user';
                                      users[name] = r.user;
                                  }
                              });
                } else {
                    if (user_type[name] === 'team') {
                        teamCard.css(pos).empty().show();
                        teamCard.append($.tmpl($('#templ-team-card'), user));
                    } else {
                        userCard.css(pos).empty().show();
                        userCard.append($.tmpl($('#templ-user-card'), user));
                    }
                }
            });
    });
});

/* @source mod/colorcube.js */;

define("mod/colorcube", 
    [
  "jquery"
],
    function ($) {
        var colorcube = {}, cubeWnd;
        var showCubeWnd = function (el) {
            el = $(el);
            if (!cubeWnd) {
                cubeWnd = $('<div id="color" class="colorcube"></div>').appendTo('body');
            }
            var pos = el.offset();
            pos = {top:pos.top - 40, left:pos.left + el.width()/2 -15};
            cubeWnd.show().offset(pos).css({'background-color':el.data('color')});
        };
        colorcube.init = function (opts) {
            if (opts.target) {
                $(opts.target).delegate(
                    '.line .color', 'mouseenter mouseleave', function (e) {
                        if (e.type === 'mouseenter') {
                            showCubeWnd(this);
                        } else {
                            cubeWnd.hide();
                        }
                    });
            }
        };
        return colorcube;
    }
);

/* @source lib/socket.io.js */;

/*! Socket.IO.js build:0.9.16, development. Copyright(c) 2011 LearnBoost <dev@learnboost.com> MIT Licensed */

var io = ('undefined' === typeof module ? {} : module.exports);
(function() {

/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, global) {

  /**
   * IO namespace.
   *
   * @namespace
   */

  var io = exports;

  /**
   * Socket.IO version
   *
   * @api public
   */

  io.version = '0.9.16';

  /**
   * Protocol implemented.
   *
   * @api public
   */

  io.protocol = 1;

  /**
   * Available transports, these will be populated with the available transports
   *
   * @api public
   */

  io.transports = [];

  /**
   * Keep track of jsonp callbacks.
   *
   * @api private
   */

  io.j = [];

  /**
   * Keep track of our io.Sockets
   *
   * @api private
   */
  io.sockets = {};


  /**
   * Manages connections to hosts.
   *
   * @param {String} uri
   * @Param {Boolean} force creation of new socket (defaults to false)
   * @api public
   */

  io.connect = function (host, details) {
    var uri = io.util.parseUri(host)
      , uuri
      , socket;

    if (global && global.location) {
      uri.protocol = uri.protocol || global.location.protocol.slice(0, -1);
      uri.host = uri.host || (global.document
        ? global.document.domain : global.location.hostname);
      uri.port = uri.port || global.location.port;
    }

    uuri = io.util.uniqueUri(uri);

    var options = {
        host: uri.host
      , secure: 'https' == uri.protocol
      , port: uri.port || ('https' == uri.protocol ? 443 : 80)
      , query: uri.query || ''
    };

    io.util.merge(options, details);

    if (options['force new connection'] || !io.sockets[uuri]) {
      socket = new io.Socket(options);
    }

    if (!options['force new connection'] && socket) {
      io.sockets[uuri] = socket;
    }

    socket = socket || io.sockets[uuri];

    // if path is different from '' or /
    return socket.of(uri.path.length > 1 ? uri.path : '');
  };

})('object' === typeof module ? module.exports : (this.io = {}), this);
/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, global) {

  /**
   * Utilities namespace.
   *
   * @namespace
   */

  var util = exports.util = {};

  /**
   * Parses an URI
   *
   * @author Steven Levithan <stevenlevithan.com> (MIT license)
   * @api public
   */

  var re = /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/;

  var parts = ['source', 'protocol', 'authority', 'userInfo', 'user', 'password',
               'host', 'port', 'relative', 'path', 'directory', 'file', 'query',
               'anchor'];

  util.parseUri = function (str) {
    var m = re.exec(str || '')
      , uri = {}
      , i = 14;

    while (i--) {
      uri[parts[i]] = m[i] || '';
    }

    return uri;
  };

  /**
   * Produces a unique url that identifies a Socket.IO connection.
   *
   * @param {Object} uri
   * @api public
   */

  util.uniqueUri = function (uri) {
    var protocol = uri.protocol
      , host = uri.host
      , port = uri.port;

    if ('document' in global) {
      host = host || document.domain;
      port = port || (protocol == 'https'
        && document.location.protocol !== 'https:' ? 443 : document.location.port);
    } else {
      host = host || 'localhost';

      if (!port && protocol == 'https') {
        port = 443;
      }
    }

    return (protocol || 'http') + '://' + host + ':' + (port || 80);
  };

  /**
   * Mergest 2 query strings in to once unique query string
   *
   * @param {String} base
   * @param {String} addition
   * @api public
   */

  util.query = function (base, addition) {
    var query = util.chunkQuery(base || '')
      , components = [];

    util.merge(query, util.chunkQuery(addition || ''));
    for (var part in query) {
      if (query.hasOwnProperty(part)) {
        components.push(part + '=' + query[part]);
      }
    }

    return components.length ? '?' + components.join('&') : '';
  };

  /**
   * Transforms a querystring in to an object
   *
   * @param {String} qs
   * @api public
   */

  util.chunkQuery = function (qs) {
    var query = {}
      , params = qs.split('&')
      , i = 0
      , l = params.length
      , kv;

    for (; i < l; ++i) {
      kv = params[i].split('=');
      if (kv[0]) {
        query[kv[0]] = kv[1];
      }
    }

    return query;
  };

  /**
   * Executes the given function when the page is loaded.
   *
   *     io.util.load(function () { console.log('page loaded'); });
   *
   * @param {Function} fn
   * @api public
   */

  var pageLoaded = false;

  util.load = function (fn) {
    if ('document' in global && document.readyState === 'complete' || pageLoaded) {
      return fn();
    }

    util.on(global, 'load', fn, false);
  };

  /**
   * Adds an event.
   *
   * @api private
   */

  util.on = function (element, event, fn, capture) {
    if (element.attachEvent) {
      element.attachEvent('on' + event, fn);
    } else if (element.addEventListener) {
      element.addEventListener(event, fn, capture);
    }
  };

  /**
   * Generates the correct `XMLHttpRequest` for regular and cross domain requests.
   *
   * @param {Boolean} [xdomain] Create a request that can be used cross domain.
   * @returns {XMLHttpRequest|false} If we can create a XMLHttpRequest.
   * @api private
   */

  util.request = function (xdomain) {

    if (xdomain && 'undefined' != typeof XDomainRequest && !util.ua.hasCORS) {
      return new XDomainRequest();
    }

    if ('undefined' != typeof XMLHttpRequest && (!xdomain || util.ua.hasCORS)) {
      return new XMLHttpRequest();
    }

    if (!xdomain) {
      try {
        return new window[(['Active'].concat('Object').join('X'))]('Microsoft.XMLHTTP');
      } catch(e) { }
    }

    return null;
  };

  /**
   * XHR based transport constructor.
   *
   * @constructor
   * @api public
   */

  /**
   * Change the internal pageLoaded value.
   */

  if ('undefined' != typeof window) {
    util.load(function () {
      pageLoaded = true;
    });
  }

  /**
   * Defers a function to ensure a spinner is not displayed by the browser
   *
   * @param {Function} fn
   * @api public
   */

  util.defer = function (fn) {
    if (!util.ua.webkit || 'undefined' != typeof importScripts) {
      return fn();
    }

    util.load(function () {
      setTimeout(fn, 100);
    });
  };

  /**
   * Merges two objects.
   *
   * @api public
   */

  util.merge = function merge (target, additional, deep, lastseen) {
    var seen = lastseen || []
      , depth = typeof deep == 'undefined' ? 2 : deep
      , prop;

    for (prop in additional) {
      if (additional.hasOwnProperty(prop) && util.indexOf(seen, prop) < 0) {
        if (typeof target[prop] !== 'object' || !depth) {
          target[prop] = additional[prop];
          seen.push(additional[prop]);
        } else {
          util.merge(target[prop], additional[prop], depth - 1, seen);
        }
      }
    }

    return target;
  };

  /**
   * Merges prototypes from objects
   *
   * @api public
   */

  util.mixin = function (ctor, ctor2) {
    util.merge(ctor.prototype, ctor2.prototype);
  };

  /**
   * Shortcut for prototypical and static inheritance.
   *
   * @api private
   */

  util.inherit = function (ctor, ctor2) {
    function f() {};
    f.prototype = ctor2.prototype;
    ctor.prototype = new f;
  };

  /**
   * Checks if the given object is an Array.
   *
   *     io.util.isArray([]); // true
   *     io.util.isArray({}); // false
   *
   * @param Object obj
   * @api public
   */

  util.isArray = Array.isArray || function (obj) {
    return Object.prototype.toString.call(obj) === '[object Array]';
  };

  /**
   * Intersects values of two arrays into a third
   *
   * @api public
   */

  util.intersect = function (arr, arr2) {
    var ret = []
      , longest = arr.length > arr2.length ? arr : arr2
      , shortest = arr.length > arr2.length ? arr2 : arr;

    for (var i = 0, l = shortest.length; i < l; i++) {
      if (~util.indexOf(longest, shortest[i]))
        ret.push(shortest[i]);
    }

    return ret;
  };

  /**
   * Array indexOf compatibility.
   *
   * @see bit.ly/a5Dxa2
   * @api public
   */

  util.indexOf = function (arr, o, i) {

    for (var j = arr.length, i = i < 0 ? i + j < 0 ? 0 : i + j : i || 0;
         i < j && arr[i] !== o; i++) {}

    return j <= i ? -1 : i;
  };

  /**
   * Converts enumerables to array.
   *
   * @api public
   */

  util.toArray = function (enu) {
    var arr = [];

    for (var i = 0, l = enu.length; i < l; i++)
      arr.push(enu[i]);

    return arr;
  };

  /**
   * UA / engines detection namespace.
   *
   * @namespace
   */

  util.ua = {};

  /**
   * Whether the UA supports CORS for XHR.
   *
   * @api public
   */

  util.ua.hasCORS = 'undefined' != typeof XMLHttpRequest && (function () {
    try {
      var a = new XMLHttpRequest();
    } catch (e) {
      return false;
    }

    return a.withCredentials != undefined;
  })();

  /**
   * Detect webkit.
   *
   * @api public
   */

  util.ua.webkit = 'undefined' != typeof navigator
    && /webkit/i.test(navigator.userAgent);

   /**
   * Detect iPad/iPhone/iPod.
   *
   * @api public
   */

  util.ua.iDevice = 'undefined' != typeof navigator
      && /iPad|iPhone|iPod/i.test(navigator.userAgent);

})('undefined' != typeof io ? io : module.exports, this);
/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, io) {

  /**
   * Expose constructor.
   */

  exports.EventEmitter = EventEmitter;

  /**
   * Event emitter constructor.
   *
   * @api public.
   */

  function EventEmitter () {};

  /**
   * Adds a listener
   *
   * @api public
   */

  EventEmitter.prototype.on = function (name, fn) {
    if (!this.$events) {
      this.$events = {};
    }

    if (!this.$events[name]) {
      this.$events[name] = fn;
    } else if (io.util.isArray(this.$events[name])) {
      this.$events[name].push(fn);
    } else {
      this.$events[name] = [this.$events[name], fn];
    }

    return this;
  };

  EventEmitter.prototype.addListener = EventEmitter.prototype.on;

  /**
   * Adds a volatile listener.
   *
   * @api public
   */

  EventEmitter.prototype.once = function (name, fn) {
    var self = this;

    function on () {
      self.removeListener(name, on);
      fn.apply(this, arguments);
    };

    on.listener = fn;
    this.on(name, on);

    return this;
  };

  /**
   * Removes a listener.
   *
   * @api public
   */

  EventEmitter.prototype.removeListener = function (name, fn) {
    if (this.$events && this.$events[name]) {
      var list = this.$events[name];

      if (io.util.isArray(list)) {
        var pos = -1;

        for (var i = 0, l = list.length; i < l; i++) {
          if (list[i] === fn || (list[i].listener && list[i].listener === fn)) {
            pos = i;
            break;
          }
        }

        if (pos < 0) {
          return this;
        }

        list.splice(pos, 1);

        if (!list.length) {
          delete this.$events[name];
        }
      } else if (list === fn || (list.listener && list.listener === fn)) {
        delete this.$events[name];
      }
    }

    return this;
  };

  /**
   * Removes all listeners for an event.
   *
   * @api public
   */

  EventEmitter.prototype.removeAllListeners = function (name) {
    if (name === undefined) {
      this.$events = {};
      return this;
    }

    if (this.$events && this.$events[name]) {
      this.$events[name] = null;
    }

    return this;
  };

  /**
   * Gets all listeners for a certain event.
   *
   * @api publci
   */

  EventEmitter.prototype.listeners = function (name) {
    if (!this.$events) {
      this.$events = {};
    }

    if (!this.$events[name]) {
      this.$events[name] = [];
    }

    if (!io.util.isArray(this.$events[name])) {
      this.$events[name] = [this.$events[name]];
    }

    return this.$events[name];
  };

  /**
   * Emits an event.
   *
   * @api public
   */

  EventEmitter.prototype.emit = function (name) {
    if (!this.$events) {
      return false;
    }

    var handler = this.$events[name];

    if (!handler) {
      return false;
    }

    var args = Array.prototype.slice.call(arguments, 1);

    if ('function' == typeof handler) {
      handler.apply(this, args);
    } else if (io.util.isArray(handler)) {
      var listeners = handler.slice();

      for (var i = 0, l = listeners.length; i < l; i++) {
        listeners[i].apply(this, args);
      }
    } else {
      return false;
    }

    return true;
  };

})(
    'undefined' != typeof io ? io : module.exports
  , 'undefined' != typeof io ? io : module.parent.exports
);

/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

/**
 * Based on JSON2 (http://www.JSON.org/js.html).
 */

(function (exports, nativeJSON) {
  "use strict";

  // use native JSON if it's available
  if (nativeJSON && nativeJSON.parse){
    return exports.JSON = {
      parse: nativeJSON.parse
    , stringify: nativeJSON.stringify
    };
  }

  var JSON = exports.JSON = {};

  function f(n) {
      // Format integers to have at least two digits.
      return n < 10 ? '0' + n : n;
  }

  function date(d, key) {
    return isFinite(d.valueOf()) ?
        d.getUTCFullYear()     + '-' +
        f(d.getUTCMonth() + 1) + '-' +
        f(d.getUTCDate())      + 'T' +
        f(d.getUTCHours())     + ':' +
        f(d.getUTCMinutes())   + ':' +
        f(d.getUTCSeconds())   + 'Z' : null;
  };

  var cx = /[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
      escapable = /[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
      gap,
      indent,
      meta = {    // table of character substitutions
          '\b': '\\b',
          '\t': '\\t',
          '\n': '\\n',
          '\f': '\\f',
          '\r': '\\r',
          '"' : '\\"',
          '\\': '\\\\'
      },
      rep;


  function quote(string) {

// If the string contains no control characters, no quote characters, and no
// backslash characters, then we can safely slap some quotes around it.
// Otherwise we must also replace the offending characters with safe escape
// sequences.

      escapable.lastIndex = 0;
      return escapable.test(string) ? '"' + string.replace(escapable, function (a) {
          var c = meta[a];
          return typeof c === 'string' ? c :
              '\\u' + ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
      }) + '"' : '"' + string + '"';
  }


  function str(key, holder) {

// Produce a string from holder[key].

      var i,          // The loop counter.
          k,          // The member key.
          v,          // The member value.
          length,
          mind = gap,
          partial,
          value = holder[key];

// If the value has a toJSON method, call it to obtain a replacement value.

      if (value instanceof Date) {
          value = date(key);
      }

// If we were called with a replacer function, then call the replacer to
// obtain a replacement value.

      if (typeof rep === 'function') {
          value = rep.call(holder, key, value);
      }

// What happens next depends on the value's type.

      switch (typeof value) {
      case 'string':
          return quote(value);

      case 'number':

// JSON numbers must be finite. Encode non-finite numbers as null.

          return isFinite(value) ? String(value) : 'null';

      case 'boolean':
      case 'null':

// If the value is a boolean or null, convert it to a string. Note:
// typeof null does not produce 'null'. The case is included here in
// the remote chance that this gets fixed someday.

          return String(value);

// If the type is 'object', we might be dealing with an object or an array or
// null.

      case 'object':

// Due to a specification blunder in ECMAScript, typeof null is 'object',
// so watch out for that case.

          if (!value) {
              return 'null';
          }

// Make an array to hold the partial results of stringifying this object value.

          gap += indent;
          partial = [];

// Is the value an array?

          if (Object.prototype.toString.apply(value) === '[object Array]') {

// The value is an array. Stringify every element. Use null as a placeholder
// for non-JSON values.

              length = value.length;
              for (i = 0; i < length; i += 1) {
                  partial[i] = str(i, value) || 'null';
              }

// Join all of the elements together, separated with commas, and wrap them in
// brackets.

              v = partial.length === 0 ? '[]' : gap ?
                  '[\n' + gap + partial.join(',\n' + gap) + '\n' + mind + ']' :
                  '[' + partial.join(',') + ']';
              gap = mind;
              return v;
          }

// If the replacer is an array, use it to select the members to be stringified.

          if (rep && typeof rep === 'object') {
              length = rep.length;
              for (i = 0; i < length; i += 1) {
                  if (typeof rep[i] === 'string') {
                      k = rep[i];
                      v = str(k, value);
                      if (v) {
                          partial.push(quote(k) + (gap ? ': ' : ':') + v);
                      }
                  }
              }
          } else {

// Otherwise, iterate through all of the keys in the object.

              for (k in value) {
                  if (Object.prototype.hasOwnProperty.call(value, k)) {
                      v = str(k, value);
                      if (v) {
                          partial.push(quote(k) + (gap ? ': ' : ':') + v);
                      }
                  }
              }
          }

// Join all of the member texts together, separated with commas,
// and wrap them in braces.

          v = partial.length === 0 ? '{}' : gap ?
              '{\n' + gap + partial.join(',\n' + gap) + '\n' + mind + '}' :
              '{' + partial.join(',') + '}';
          gap = mind;
          return v;
      }
  }

// If the JSON object does not yet have a stringify method, give it one.

  JSON.stringify = function (value, replacer, space) {

// The stringify method takes a value and an optional replacer, and an optional
// space parameter, and returns a JSON text. The replacer can be a function
// that can replace values, or an array of strings that will select the keys.
// A default replacer method can be provided. Use of the space parameter can
// produce text that is more easily readable.

      var i;
      gap = '';
      indent = '';

// If the space parameter is a number, make an indent string containing that
// many spaces.

      if (typeof space === 'number') {
          for (i = 0; i < space; i += 1) {
              indent += ' ';
          }

// If the space parameter is a string, it will be used as the indent string.

      } else if (typeof space === 'string') {
          indent = space;
      }

// If there is a replacer, it must be a function or an array.
// Otherwise, throw an error.

      rep = replacer;
      if (replacer && typeof replacer !== 'function' &&
              (typeof replacer !== 'object' ||
              typeof replacer.length !== 'number')) {
          throw new Error('JSON.stringify');
      }

// Make a fake root object containing our value under the key of ''.
// Return the result of stringifying the value.

      return str('', {'': value});
  };

// If the JSON object does not yet have a parse method, give it one.

  JSON.parse = function (text, reviver) {
  // The parse method takes a text and an optional reviver function, and returns
  // a JavaScript value if the text is a valid JSON text.

      var j;

      function walk(holder, key) {

  // The walk method is used to recursively walk the resulting structure so
  // that modifications can be made.

          var k, v, value = holder[key];
          if (value && typeof value === 'object') {
              for (k in value) {
                  if (Object.prototype.hasOwnProperty.call(value, k)) {
                      v = walk(value, k);
                      if (v !== undefined) {
                          value[k] = v;
                      } else {
                          delete value[k];
                      }
                  }
              }
          }
          return reviver.call(holder, key, value);
      }


  // Parsing happens in four stages. In the first stage, we replace certain
  // Unicode characters with escape sequences. JavaScript handles many characters
  // incorrectly, either silently deleting them, or treating them as line endings.

      text = String(text);
      cx.lastIndex = 0;
      if (cx.test(text)) {
          text = text.replace(cx, function (a) {
              return '\\u' +
                  ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
          });
      }

  // In the second stage, we run the text against regular expressions that look
  // for non-JSON patterns. We are especially concerned with '()' and 'new'
  // because they can cause invocation, and '=' because it can cause mutation.
  // But just to be safe, we want to reject all unexpected forms.

  // We split the second stage into 4 regexp operations in order to work around
  // crippling inefficiencies in IE's and Safari's regexp engines. First we
  // replace the JSON backslash pairs with '@' (a non-JSON character). Second, we
  // replace all simple value tokens with ']' characters. Third, we delete all
  // open brackets that follow a colon or comma or that begin the text. Finally,
  // we look to see that the remaining characters are only whitespace or ']' or
  // ',' or ':' or '{' or '}'. If that is so, then the text is safe for eval.

      if (/^[\],:{}\s]*$/
              .test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, '@')
                  .replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, ']')
                  .replace(/(?:^|:|,)(?:\s*\[)+/g, ''))) {

  // In the third stage we use the eval function to compile the text into a
  // JavaScript structure. The '{' operator is subject to a syntactic ambiguity
  // in JavaScript: it can begin a block or an object literal. We wrap the text
  // in parens to eliminate the ambiguity.

          j = eval('(' + text + ')');

  // In the optional fourth stage, we recursively walk the new structure, passing
  // each name/value pair to a reviver function for possible transformation.

          return typeof reviver === 'function' ?
              walk({'': j}, '') : j;
      }

  // If the text is not JSON parseable, then a SyntaxError is thrown.

      throw new SyntaxError('JSON.parse');
  };

})(
    'undefined' != typeof io ? io : module.exports
  , typeof JSON !== 'undefined' ? JSON : undefined
);

/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, io) {

  /**
   * Parser namespace.
   *
   * @namespace
   */

  var parser = exports.parser = {};

  /**
   * Packet types.
   */

  var packets = parser.packets = [
      'disconnect'
    , 'connect'
    , 'heartbeat'
    , 'message'
    , 'json'
    , 'event'
    , 'ack'
    , 'error'
    , 'noop'
  ];

  /**
   * Errors reasons.
   */

  var reasons = parser.reasons = [
      'transport not supported'
    , 'client not handshaken'
    , 'unauthorized'
  ];

  /**
   * Errors advice.
   */

  var advice = parser.advice = [
      'reconnect'
  ];

  /**
   * Shortcuts.
   */

  var JSON = io.JSON
    , indexOf = io.util.indexOf;

  /**
   * Encodes a packet.
   *
   * @api private
   */

  parser.encodePacket = function (packet) {
    var type = indexOf(packets, packet.type)
      , id = packet.id || ''
      , endpoint = packet.endpoint || ''
      , ack = packet.ack
      , data = null;

    switch (packet.type) {
      case 'error':
        var reason = packet.reason ? indexOf(reasons, packet.reason) : ''
          , adv = packet.advice ? indexOf(advice, packet.advice) : '';

        if (reason !== '' || adv !== '')
          data = reason + (adv !== '' ? ('+' + adv) : '');

        break;

      case 'message':
        if (packet.data !== '')
          data = packet.data;
        break;

      case 'event':
        var ev = { name: packet.name };

        if (packet.args && packet.args.length) {
          ev.args = packet.args;
        }

        data = JSON.stringify(ev);
        break;

      case 'json':
        data = JSON.stringify(packet.data);
        break;

      case 'connect':
        if (packet.qs)
          data = packet.qs;
        break;

      case 'ack':
        data = packet.ackId
          + (packet.args && packet.args.length
              ? '+' + JSON.stringify(packet.args) : '');
        break;
    }

    // construct packet with required fragments
    var encoded = [
        type
      , id + (ack == 'data' ? '+' : '')
      , endpoint
    ];

    // data fragment is optional
    if (data !== null && data !== undefined)
      encoded.push(data);

    return encoded.join(':');
  };

  /**
   * Encodes multiple messages (payload).
   *
   * @param {Array} messages
   * @api private
   */

  parser.encodePayload = function (packets) {
    var decoded = '';

    if (packets.length == 1)
      return packets[0];

    for (var i = 0, l = packets.length; i < l; i++) {
      var packet = packets[i];
      decoded += '\ufffd' + packet.length + '\ufffd' + packets[i];
    }

    return decoded;
  };

  /**
   * Decodes a packet
   *
   * @api private
   */

  var regexp = /([^:]+):([0-9]+)?(\+)?:([^:]+)?:?([\s\S]*)?/;

  parser.decodePacket = function (data) {
    var pieces = data.match(regexp);

    if (!pieces) return {};

    var id = pieces[2] || ''
      , data = pieces[5] || ''
      , packet = {
            type: packets[pieces[1]]
          , endpoint: pieces[4] || ''
        };

    // whether we need to acknowledge the packet
    if (id) {
      packet.id = id;
      if (pieces[3])
        packet.ack = 'data';
      else
        packet.ack = true;
    }

    // handle different packet types
    switch (packet.type) {
      case 'error':
        var pieces = data.split('+');
        packet.reason = reasons[pieces[0]] || '';
        packet.advice = advice[pieces[1]] || '';
        break;

      case 'message':
        packet.data = data || '';
        break;

      case 'event':
        try {
          var opts = JSON.parse(data);
          packet.name = opts.name;
          packet.args = opts.args;
        } catch (e) { }

        packet.args = packet.args || [];
        break;

      case 'json':
        try {
          packet.data = JSON.parse(data);
        } catch (e) { }
        break;

      case 'connect':
        packet.qs = data || '';
        break;

      case 'ack':
        var pieces = data.match(/^([0-9]+)(\+)?(.*)/);
        if (pieces) {
          packet.ackId = pieces[1];
          packet.args = [];

          if (pieces[3]) {
            try {
              packet.args = pieces[3] ? JSON.parse(pieces[3]) : [];
            } catch (e) { }
          }
        }
        break;

      case 'disconnect':
      case 'heartbeat':
        break;
    };

    return packet;
  };

  /**
   * Decodes data payload. Detects multiple messages
   *
   * @return {Array} messages
   * @api public
   */

  parser.decodePayload = function (data) {
    // IE doesn't like data[i] for unicode chars, charAt works fine
    if (data.charAt(0) == '\ufffd') {
      var ret = [];

      for (var i = 1, length = ''; i < data.length; i++) {
        if (data.charAt(i) == '\ufffd') {
          ret.push(parser.decodePacket(data.substr(i + 1).substr(0, length)));
          i += Number(length) + 1;
          length = '';
        } else {
          length += data.charAt(i);
        }
      }

      return ret;
    } else {
      return [parser.decodePacket(data)];
    }
  };

})(
    'undefined' != typeof io ? io : module.exports
  , 'undefined' != typeof io ? io : module.parent.exports
);
/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, io) {

  /**
   * Expose constructor.
   */

  exports.Transport = Transport;

  /**
   * This is the transport template for all supported transport methods.
   *
   * @constructor
   * @api public
   */

  function Transport (socket, sessid) {
    this.socket = socket;
    this.sessid = sessid;
  };

  /**
   * Apply EventEmitter mixin.
   */

  io.util.mixin(Transport, io.EventEmitter);


  /**
   * Indicates whether heartbeats is enabled for this transport
   *
   * @api private
   */

  Transport.prototype.heartbeats = function () {
    return true;
  };

  /**
   * Handles the response from the server. When a new response is received
   * it will automatically update the timeout, decode the message and
   * forwards the response to the onMessage function for further processing.
   *
   * @param {String} data Response from the server.
   * @api private
   */

  Transport.prototype.onData = function (data) {
    this.clearCloseTimeout();

    // If the connection in currently open (or in a reopening state) reset the close
    // timeout since we have just received data. This check is necessary so
    // that we don't reset the timeout on an explicitly disconnected connection.
    if (this.socket.connected || this.socket.connecting || this.socket.reconnecting) {
      this.setCloseTimeout();
    }

    if (data !== '') {
      // todo: we should only do decodePayload for xhr transports
      var msgs = io.parser.decodePayload(data);

      if (msgs && msgs.length) {
        for (var i = 0, l = msgs.length; i < l; i++) {
          this.onPacket(msgs[i]);
        }
      }
    }

    return this;
  };

  /**
   * Handles packets.
   *
   * @api private
   */

  Transport.prototype.onPacket = function (packet) {
    this.socket.setHeartbeatTimeout();

    if (packet.type == 'heartbeat') {
      return this.onHeartbeat();
    }

    if (packet.type == 'connect' && packet.endpoint == '') {
      this.onConnect();
    }

    if (packet.type == 'error' && packet.advice == 'reconnect') {
      this.isOpen = false;
    }

    this.socket.onPacket(packet);

    return this;
  };

  /**
   * Sets close timeout
   *
   * @api private
   */

  Transport.prototype.setCloseTimeout = function () {
    if (!this.closeTimeout) {
      var self = this;

      this.closeTimeout = setTimeout(function () {
        self.onDisconnect();
      }, this.socket.closeTimeout);
    }
  };

  /**
   * Called when transport disconnects.
   *
   * @api private
   */

  Transport.prototype.onDisconnect = function () {
    if (this.isOpen) this.close();
    this.clearTimeouts();
    this.socket.onDisconnect();
    return this;
  };

  /**
   * Called when transport connects
   *
   * @api private
   */

  Transport.prototype.onConnect = function () {
    this.socket.onConnect();
    return this;
  };

  /**
   * Clears close timeout
   *
   * @api private
   */

  Transport.prototype.clearCloseTimeout = function () {
    if (this.closeTimeout) {
      clearTimeout(this.closeTimeout);
      this.closeTimeout = null;
    }
  };

  /**
   * Clear timeouts
   *
   * @api private
   */

  Transport.prototype.clearTimeouts = function () {
    this.clearCloseTimeout();

    if (this.reopenTimeout) {
      clearTimeout(this.reopenTimeout);
    }
  };

  /**
   * Sends a packet
   *
   * @param {Object} packet object.
   * @api private
   */

  Transport.prototype.packet = function (packet) {
    this.send(io.parser.encodePacket(packet));
  };

  /**
   * Send the received heartbeat message back to server. So the server
   * knows we are still connected.
   *
   * @param {String} heartbeat Heartbeat response from the server.
   * @api private
   */

  Transport.prototype.onHeartbeat = function (heartbeat) {
    this.packet({ type: 'heartbeat' });
  };

  /**
   * Called when the transport opens.
   *
   * @api private
   */

  Transport.prototype.onOpen = function () {
    this.isOpen = true;
    this.clearCloseTimeout();
    this.socket.onOpen();
  };

  /**
   * Notifies the base when the connection with the Socket.IO server
   * has been disconnected.
   *
   * @api private
   */

  Transport.prototype.onClose = function () {
    var self = this;

    /* FIXME: reopen delay causing a infinit loop
    this.reopenTimeout = setTimeout(function () {
      self.open();
    }, this.socket.options['reopen delay']);*/

    this.isOpen = false;
    this.socket.onClose();
    this.onDisconnect();
  };

  /**
   * Generates a connection url based on the Socket.IO URL Protocol.
   * See <https://github.com/learnboost/socket.io-node/> for more details.
   *
   * @returns {String} Connection url
   * @api private
   */

  Transport.prototype.prepareUrl = function () {
    var options = this.socket.options;

    return this.scheme() + '://'
      + options.host + ':' + options.port + '/'
      + options.resource + '/' + io.protocol
      + '/' + this.name + '/' + this.sessid;
  };

  /**
   * Checks if the transport is ready to start a connection.
   *
   * @param {Socket} socket The socket instance that needs a transport
   * @param {Function} fn The callback
   * @api private
   */

  Transport.prototype.ready = function (socket, fn) {
    fn.call(this);
  };
})(
    'undefined' != typeof io ? io : module.exports
  , 'undefined' != typeof io ? io : module.parent.exports
);
/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, io, global) {

  /**
   * Expose constructor.
   */

  exports.Socket = Socket;

  /**
   * Create a new `Socket.IO client` which can establish a persistent
   * connection with a Socket.IO enabled server.
   *
   * @api public
   */

  function Socket (options) {
    this.options = {
        port: 80
      , secure: false
      , document: 'document' in global ? document : false
      , resource: 'socket.io'
      , transports: io.transports
      , 'connect timeout': 10000
      , 'try multiple transports': true
      , 'reconnect': true
      , 'reconnection delay': 500
      , 'reconnection limit': Infinity
      , 'reopen delay': 3000
      , 'max reconnection attempts': 10
      , 'sync disconnect on unload': false
      , 'auto connect': true
      , 'flash policy port': 10843
      , 'manualFlush': false
    };

    io.util.merge(this.options, options);

    this.connected = false;
    this.open = false;
    this.connecting = false;
    this.reconnecting = false;
    this.namespaces = {};
    this.buffer = [];
    this.doBuffer = false;

    if (this.options['sync disconnect on unload'] &&
        (!this.isXDomain() || io.util.ua.hasCORS)) {
      var self = this;
      io.util.on(global, 'beforeunload', function () {
        self.disconnectSync();
      }, false);
    }

    if (this.options['auto connect']) {
      this.connect();
    }
};

  /**
   * Apply EventEmitter mixin.
   */

  io.util.mixin(Socket, io.EventEmitter);

  /**
   * Returns a namespace listener/emitter for this socket
   *
   * @api public
   */

  Socket.prototype.of = function (name) {
    if (!this.namespaces[name]) {
      this.namespaces[name] = new io.SocketNamespace(this, name);

      if (name !== '') {
        this.namespaces[name].packet({ type: 'connect' });
      }
    }

    return this.namespaces[name];
  };

  /**
   * Emits the given event to the Socket and all namespaces
   *
   * @api private
   */

  Socket.prototype.publish = function () {
    this.emit.apply(this, arguments);

    var nsp;

    for (var i in this.namespaces) {
      if (this.namespaces.hasOwnProperty(i)) {
        nsp = this.of(i);
        nsp.$emit.apply(nsp, arguments);
      }
    }
  };

  /**
   * Performs the handshake
   *
   * @api private
   */

  function empty () { };

  Socket.prototype.handshake = function (fn) {
    var self = this
      , options = this.options;

    function complete (data) {
      if (data instanceof Error) {
        self.connecting = false;
        self.onError(data.message);
      } else {
        fn.apply(null, data.split(':'));
      }
    };

    var url = [
          'http' + (options.secure ? 's' : '') + ':/'
        , options.host + ':' + options.port
        , options.resource
        , io.protocol
        , io.util.query(this.options.query, 't=' + +new Date)
      ].join('/');

    if (this.isXDomain() && !io.util.ua.hasCORS) {
      var insertAt = document.getElementsByTagName('script')[0]
        , script = document.createElement('script');

      script.src = url + '&jsonp=' + io.j.length;
      insertAt.parentNode.insertBefore(script, insertAt);

      io.j.push(function (data) {
        complete(data);
        script.parentNode.removeChild(script);
      });
    } else {
      var xhr = io.util.request();

      xhr.open('GET', url, true);
      if (this.isXDomain()) {
        xhr.withCredentials = true;
      }
      xhr.onreadystatechange = function () {
        if (xhr.readyState == 4) {
          xhr.onreadystatechange = empty;

          if (xhr.status == 200) {
            complete(xhr.responseText);
          } else if (xhr.status == 403) {
            self.onError(xhr.responseText);
          } else {
            self.connecting = false;            
            !self.reconnecting && self.onError(xhr.responseText);
          }
        }
      };
      xhr.send(null);
    }
  };

  /**
   * Find an available transport based on the options supplied in the constructor.
   *
   * @api private
   */

  Socket.prototype.getTransport = function (override) {
    var transports = override || this.transports, match;

    for (var i = 0, transport; transport = transports[i]; i++) {
      if (io.Transport[transport]
        && io.Transport[transport].check(this)
        && (!this.isXDomain() || io.Transport[transport].xdomainCheck(this))) {
        return new io.Transport[transport](this, this.sessionid);
      }
    }

    return null;
  };

  /**
   * Connects to the server.
   *
   * @param {Function} [fn] Callback.
   * @returns {io.Socket}
   * @api public
   */

  Socket.prototype.connect = function (fn) {
    if (this.connecting) {
      return this;
    }

    var self = this;
    self.connecting = true;
    
    this.handshake(function (sid, heartbeat, close, transports) {
      self.sessionid = sid;
      self.closeTimeout = close * 1000;
      self.heartbeatTimeout = heartbeat * 1000;
      if(!self.transports)
          self.transports = self.origTransports = (transports ? io.util.intersect(
              transports.split(',')
            , self.options.transports
          ) : self.options.transports);

      self.setHeartbeatTimeout();

      function connect (transports){
        if (self.transport) self.transport.clearTimeouts();

        self.transport = self.getTransport(transports);
        if (!self.transport) return self.publish('connect_failed');

        // once the transport is ready
        self.transport.ready(self, function () {
          self.connecting = true;
          self.publish('connecting', self.transport.name);
          self.transport.open();

          if (self.options['connect timeout']) {
            self.connectTimeoutTimer = setTimeout(function () {
              if (!self.connected) {
                self.connecting = false;

                if (self.options['try multiple transports']) {
                  var remaining = self.transports;

                  while (remaining.length > 0 && remaining.splice(0,1)[0] !=
                         self.transport.name) {}

                    if (remaining.length){
                      connect(remaining);
                    } else {
                      self.publish('connect_failed');
                    }
                }
              }
            }, self.options['connect timeout']);
          }
        });
      }

      connect(self.transports);

      self.once('connect', function (){
        clearTimeout(self.connectTimeoutTimer);

        fn && typeof fn == 'function' && fn();
      });
    });

    return this;
  };

  /**
   * Clears and sets a new heartbeat timeout using the value given by the
   * server during the handshake.
   *
   * @api private
   */

  Socket.prototype.setHeartbeatTimeout = function () {
    clearTimeout(this.heartbeatTimeoutTimer);
    if(this.transport && !this.transport.heartbeats()) return;

    var self = this;
    this.heartbeatTimeoutTimer = setTimeout(function () {
      self.transport.onClose();
    }, this.heartbeatTimeout);
  };

  /**
   * Sends a message.
   *
   * @param {Object} data packet.
   * @returns {io.Socket}
   * @api public
   */

  Socket.prototype.packet = function (data) {
    if (this.connected && !this.doBuffer) {
      this.transport.packet(data);
    } else {
      this.buffer.push(data);
    }

    return this;
  };

  /**
   * Sets buffer state
   *
   * @api private
   */

  Socket.prototype.setBuffer = function (v) {
    this.doBuffer = v;

    if (!v && this.connected && this.buffer.length) {
      if (!this.options['manualFlush']) {
        this.flushBuffer();
      }
    }
  };

  /**
   * Flushes the buffer data over the wire.
   * To be invoked manually when 'manualFlush' is set to true.
   *
   * @api public
   */

  Socket.prototype.flushBuffer = function() {
    this.transport.payload(this.buffer);
    this.buffer = [];
  };
  

  /**
   * Disconnect the established connect.
   *
   * @returns {io.Socket}
   * @api public
   */

  Socket.prototype.disconnect = function () {
    if (this.connected || this.connecting) {
      if (this.open) {
        this.of('').packet({ type: 'disconnect' });
      }

      // handle disconnection immediately
      this.onDisconnect('booted');
    }

    return this;
  };

  /**
   * Disconnects the socket with a sync XHR.
   *
   * @api private
   */

  Socket.prototype.disconnectSync = function () {
    // ensure disconnection
    var xhr = io.util.request();
    var uri = [
        'http' + (this.options.secure ? 's' : '') + ':/'
      , this.options.host + ':' + this.options.port
      , this.options.resource
      , io.protocol
      , ''
      , this.sessionid
    ].join('/') + '/?disconnect=1';

    xhr.open('GET', uri, false);
    xhr.send(null);

    // handle disconnection immediately
    this.onDisconnect('booted');
  };

  /**
   * Check if we need to use cross domain enabled transports. Cross domain would
   * be a different port or different domain name.
   *
   * @returns {Boolean}
   * @api private
   */

  Socket.prototype.isXDomain = function () {

    var port = global.location.port ||
      ('https:' == global.location.protocol ? 443 : 80);

    return this.options.host !== global.location.hostname 
      || this.options.port != port;
  };

  /**
   * Called upon handshake.
   *
   * @api private
   */

  Socket.prototype.onConnect = function () {
    if (!this.connected) {
      this.connected = true;
      this.connecting = false;
      if (!this.doBuffer) {
        // make sure to flush the buffer
        this.setBuffer(false);
      }
      this.emit('connect');
    }
  };

  /**
   * Called when the transport opens
   *
   * @api private
   */

  Socket.prototype.onOpen = function () {
    this.open = true;
  };

  /**
   * Called when the transport closes.
   *
   * @api private
   */

  Socket.prototype.onClose = function () {
    this.open = false;
    clearTimeout(this.heartbeatTimeoutTimer);
  };

  /**
   * Called when the transport first opens a connection
   *
   * @param text
   */

  Socket.prototype.onPacket = function (packet) {
    this.of(packet.endpoint).onPacket(packet);
  };

  /**
   * Handles an error.
   *
   * @api private
   */

  Socket.prototype.onError = function (err) {
    if (err && err.advice) {
      if (err.advice === 'reconnect' && (this.connected || this.connecting)) {
        this.disconnect();
        if (this.options.reconnect) {
          this.reconnect();
        }
      }
    }

    this.publish('error', err && err.reason ? err.reason : err);
  };

  /**
   * Called when the transport disconnects.
   *
   * @api private
   */

  Socket.prototype.onDisconnect = function (reason) {
    var wasConnected = this.connected
      , wasConnecting = this.connecting;

    this.connected = false;
    this.connecting = false;
    this.open = false;

    if (wasConnected || wasConnecting) {
      this.transport.close();
      this.transport.clearTimeouts();
      if (wasConnected) {
        this.publish('disconnect', reason);

        if ('booted' != reason && this.options.reconnect && !this.reconnecting) {
          this.reconnect();
        }
      }
    }
  };

  /**
   * Called upon reconnection.
   *
   * @api private
   */

  Socket.prototype.reconnect = function () {
    this.reconnecting = true;
    this.reconnectionAttempts = 0;
    this.reconnectionDelay = this.options['reconnection delay'];

    var self = this
      , maxAttempts = this.options['max reconnection attempts']
      , tryMultiple = this.options['try multiple transports']
      , limit = this.options['reconnection limit'];

    function reset () {
      if (self.connected) {
        for (var i in self.namespaces) {
          if (self.namespaces.hasOwnProperty(i) && '' !== i) {
              self.namespaces[i].packet({ type: 'connect' });
          }
        }
        self.publish('reconnect', self.transport.name, self.reconnectionAttempts);
      }

      clearTimeout(self.reconnectionTimer);

      self.removeListener('connect_failed', maybeReconnect);
      self.removeListener('connect', maybeReconnect);

      self.reconnecting = false;

      delete self.reconnectionAttempts;
      delete self.reconnectionDelay;
      delete self.reconnectionTimer;
      delete self.redoTransports;

      self.options['try multiple transports'] = tryMultiple;
    };

    function maybeReconnect () {
      if (!self.reconnecting) {
        return;
      }

      if (self.connected) {
        return reset();
      };

      if (self.connecting && self.reconnecting) {
        return self.reconnectionTimer = setTimeout(maybeReconnect, 1000);
      }

      if (self.reconnectionAttempts++ >= maxAttempts) {
        if (!self.redoTransports) {
          self.on('connect_failed', maybeReconnect);
          self.options['try multiple transports'] = true;
          self.transports = self.origTransports;
          self.transport = self.getTransport();
          self.redoTransports = true;
          self.connect();
        } else {
          self.publish('reconnect_failed');
          reset();
        }
      } else {
        if (self.reconnectionDelay < limit) {
          self.reconnectionDelay *= 2; // exponential back off
        }

        self.connect();
        self.publish('reconnecting', self.reconnectionDelay, self.reconnectionAttempts);
        self.reconnectionTimer = setTimeout(maybeReconnect, self.reconnectionDelay);
      }
    };

    this.options['try multiple transports'] = false;
    this.reconnectionTimer = setTimeout(maybeReconnect, this.reconnectionDelay);

    this.on('connect', maybeReconnect);
  };

})(
    'undefined' != typeof io ? io : module.exports
  , 'undefined' != typeof io ? io : module.parent.exports
  , this
);
/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, io) {

  /**
   * Expose constructor.
   */

  exports.SocketNamespace = SocketNamespace;

  /**
   * Socket namespace constructor.
   *
   * @constructor
   * @api public
   */

  function SocketNamespace (socket, name) {
    this.socket = socket;
    this.name = name || '';
    this.flags = {};
    this.json = new Flag(this, 'json');
    this.ackPackets = 0;
    this.acks = {};
  };

  /**
   * Apply EventEmitter mixin.
   */

  io.util.mixin(SocketNamespace, io.EventEmitter);

  /**
   * Copies emit since we override it
   *
   * @api private
   */

  SocketNamespace.prototype.$emit = io.EventEmitter.prototype.emit;

  /**
   * Creates a new namespace, by proxying the request to the socket. This
   * allows us to use the synax as we do on the server.
   *
   * @api public
   */

  SocketNamespace.prototype.of = function () {
    return this.socket.of.apply(this.socket, arguments);
  };

  /**
   * Sends a packet.
   *
   * @api private
   */

  SocketNamespace.prototype.packet = function (packet) {
    packet.endpoint = this.name;
    this.socket.packet(packet);
    this.flags = {};
    return this;
  };

  /**
   * Sends a message
   *
   * @api public
   */

  SocketNamespace.prototype.send = function (data, fn) {
    var packet = {
        type: this.flags.json ? 'json' : 'message'
      , data: data
    };

    if ('function' == typeof fn) {
      packet.id = ++this.ackPackets;
      packet.ack = true;
      this.acks[packet.id] = fn;
    }

    return this.packet(packet);
  };

  /**
   * Emits an event
   *
   * @api public
   */
  
  SocketNamespace.prototype.emit = function (name) {
    var args = Array.prototype.slice.call(arguments, 1)
      , lastArg = args[args.length - 1]
      , packet = {
            type: 'event'
          , name: name
        };

    if ('function' == typeof lastArg) {
      packet.id = ++this.ackPackets;
      packet.ack = 'data';
      this.acks[packet.id] = lastArg;
      args = args.slice(0, args.length - 1);
    }

    packet.args = args;

    return this.packet(packet);
  };

  /**
   * Disconnects the namespace
   *
   * @api private
   */

  SocketNamespace.prototype.disconnect = function () {
    if (this.name === '') {
      this.socket.disconnect();
    } else {
      this.packet({ type: 'disconnect' });
      this.$emit('disconnect');
    }

    return this;
  };

  /**
   * Handles a packet
   *
   * @api private
   */

  SocketNamespace.prototype.onPacket = function (packet) {
    var self = this;

    function ack () {
      self.packet({
          type: 'ack'
        , args: io.util.toArray(arguments)
        , ackId: packet.id
      });
    };

    switch (packet.type) {
      case 'connect':
        this.$emit('connect');
        break;

      case 'disconnect':
        if (this.name === '') {
          this.socket.onDisconnect(packet.reason || 'booted');
        } else {
          this.$emit('disconnect', packet.reason);
        }
        break;

      case 'message':
      case 'json':
        var params = ['message', packet.data];

        if (packet.ack == 'data') {
          params.push(ack);
        } else if (packet.ack) {
          this.packet({ type: 'ack', ackId: packet.id });
        }

        this.$emit.apply(this, params);
        break;

      case 'event':
        var params = [packet.name].concat(packet.args);

        if (packet.ack == 'data')
          params.push(ack);

        this.$emit.apply(this, params);
        break;

      case 'ack':
        if (this.acks[packet.ackId]) {
          this.acks[packet.ackId].apply(this, packet.args);
          delete this.acks[packet.ackId];
        }
        break;

      case 'error':
        if (packet.advice){
          this.socket.onError(packet);
        } else {
          if (packet.reason == 'unauthorized') {
            this.$emit('connect_failed', packet.reason);
          } else {
            this.$emit('error', packet.reason);
          }
        }
        break;
    }
  };

  /**
   * Flag interface.
   *
   * @api private
   */

  function Flag (nsp, name) {
    this.namespace = nsp;
    this.name = name;
  };

  /**
   * Send a message
   *
   * @api public
   */

  Flag.prototype.send = function () {
    this.namespace.flags[this.name] = true;
    this.namespace.send.apply(this.namespace, arguments);
  };

  /**
   * Emit an event
   *
   * @api public
   */

  Flag.prototype.emit = function () {
    this.namespace.flags[this.name] = true;
    this.namespace.emit.apply(this.namespace, arguments);
  };

})(
    'undefined' != typeof io ? io : module.exports
  , 'undefined' != typeof io ? io : module.parent.exports
);

/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, io, global) {

  /**
   * Expose constructor.
   */

  exports.websocket = WS;

  /**
   * The WebSocket transport uses the HTML5 WebSocket API to establish an
   * persistent connection with the Socket.IO server. This transport will also
   * be inherited by the FlashSocket fallback as it provides a API compatible
   * polyfill for the WebSockets.
   *
   * @constructor
   * @extends {io.Transport}
   * @api public
   */

  function WS (socket) {
    io.Transport.apply(this, arguments);
  };

  /**
   * Inherits from Transport.
   */

  io.util.inherit(WS, io.Transport);

  /**
   * Transport name
   *
   * @api public
   */

  WS.prototype.name = 'websocket';

  /**
   * Initializes a new `WebSocket` connection with the Socket.IO server. We attach
   * all the appropriate listeners to handle the responses from the server.
   *
   * @returns {Transport}
   * @api public
   */

  WS.prototype.open = function () {
    var query = io.util.query(this.socket.options.query)
      , self = this
      , Socket


    if (!Socket) {
      Socket = global.MozWebSocket || global.WebSocket;
    }

    this.websocket = new Socket(this.prepareUrl() + query);

    this.websocket.onopen = function () {
      self.onOpen();
      self.socket.setBuffer(false);
    };
    this.websocket.onmessage = function (ev) {
      self.onData(ev.data);
    };
    this.websocket.onclose = function () {
      self.onClose();
      self.socket.setBuffer(true);
    };
    this.websocket.onerror = function (e) {
      self.onError(e);
    };

    return this;
  };

  /**
   * Send a message to the Socket.IO server. The message will automatically be
   * encoded in the correct message format.
   *
   * @returns {Transport}
   * @api public
   */

  // Do to a bug in the current IDevices browser, we need to wrap the send in a 
  // setTimeout, when they resume from sleeping the browser will crash if 
  // we don't allow the browser time to detect the socket has been closed
  if (io.util.ua.iDevice) {
    WS.prototype.send = function (data) {
      var self = this;
      setTimeout(function() {
         self.websocket.send(data);
      },0);
      return this;
    };
  } else {
    WS.prototype.send = function (data) {
      this.websocket.send(data);
      return this;
    };
  }

  /**
   * Payload
   *
   * @api private
   */

  WS.prototype.payload = function (arr) {
    for (var i = 0, l = arr.length; i < l; i++) {
      this.packet(arr[i]);
    }
    return this;
  };

  /**
   * Disconnect the established `WebSocket` connection.
   *
   * @returns {Transport}
   * @api public
   */

  WS.prototype.close = function () {
    this.websocket.close();
    return this;
  };

  /**
   * Handle the errors that `WebSocket` might be giving when we
   * are attempting to connect or send messages.
   *
   * @param {Error} e The error.
   * @api private
   */

  WS.prototype.onError = function (e) {
    this.socket.onError(e);
  };

  /**
   * Returns the appropriate scheme for the URI generation.
   *
   * @api private
   */
  WS.prototype.scheme = function () {
    return this.socket.options.secure ? 'wss' : 'ws';
  };

  /**
   * Checks if the browser has support for native `WebSockets` and that
   * it's not the polyfill created for the FlashSocket transport.
   *
   * @return {Boolean}
   * @api public
   */

  WS.check = function () {
    return ('WebSocket' in global && !('__addTask' in WebSocket))
          || 'MozWebSocket' in global;
  };

  /**
   * Check if the `WebSocket` transport support cross domain communications.
   *
   * @returns {Boolean}
   * @api public
   */

  WS.xdomainCheck = function () {
    return true;
  };

  /**
   * Add the transport to your public io.transports array.
   *
   * @api private
   */

  io.transports.push('websocket');

})(
    'undefined' != typeof io ? io.Transport : module.exports
  , 'undefined' != typeof io ? io : module.parent.exports
  , this
);

/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, io) {

  /**
   * Expose constructor.
   */

  exports.flashsocket = Flashsocket;

  /**
   * The FlashSocket transport. This is a API wrapper for the HTML5 WebSocket
   * specification. It uses a .swf file to communicate with the server. If you want
   * to serve the .swf file from a other server than where the Socket.IO script is
   * coming from you need to use the insecure version of the .swf. More information
   * about this can be found on the github page.
   *
   * @constructor
   * @extends {io.Transport.websocket}
   * @api public
   */

  function Flashsocket () {
    io.Transport.websocket.apply(this, arguments);
  };

  /**
   * Inherits from Transport.
   */

  io.util.inherit(Flashsocket, io.Transport.websocket);

  /**
   * Transport name
   *
   * @api public
   */

  Flashsocket.prototype.name = 'flashsocket';

  /**
   * Disconnect the established `FlashSocket` connection. This is done by adding a 
   * new task to the FlashSocket. The rest will be handled off by the `WebSocket` 
   * transport.
   *
   * @returns {Transport}
   * @api public
   */

  Flashsocket.prototype.open = function () {
    var self = this
      , args = arguments;

    WebSocket.__addTask(function () {
      io.Transport.websocket.prototype.open.apply(self, args);
    });
    return this;
  };
  
  /**
   * Sends a message to the Socket.IO server. This is done by adding a new
   * task to the FlashSocket. The rest will be handled off by the `WebSocket` 
   * transport.
   *
   * @returns {Transport}
   * @api public
   */

  Flashsocket.prototype.send = function () {
    var self = this, args = arguments;
    WebSocket.__addTask(function () {
      io.Transport.websocket.prototype.send.apply(self, args);
    });
    return this;
  };

  /**
   * Disconnects the established `FlashSocket` connection.
   *
   * @returns {Transport}
   * @api public
   */

  Flashsocket.prototype.close = function () {
    WebSocket.__tasks.length = 0;
    io.Transport.websocket.prototype.close.call(this);
    return this;
  };

  /**
   * The WebSocket fall back needs to append the flash container to the body
   * element, so we need to make sure we have access to it. Or defer the call
   * until we are sure there is a body element.
   *
   * @param {Socket} socket The socket instance that needs a transport
   * @param {Function} fn The callback
   * @api private
   */

  Flashsocket.prototype.ready = function (socket, fn) {
    function init () {
      var options = socket.options
        , port = options['flash policy port']
        , path = [
              'http' + (options.secure ? 's' : '') + ':/'
            , options.host + ':' + options.port
            , options.resource
            , 'static/flashsocket'
            , 'WebSocketMain' + (socket.isXDomain() ? 'Insecure' : '') + '.swf'
          ];

      // Only start downloading the swf file when the checked that this browser
      // actually supports it
      if (!Flashsocket.loaded) {
        if (typeof WEB_SOCKET_SWF_LOCATION === 'undefined') {
          // Set the correct file based on the XDomain settings
          WEB_SOCKET_SWF_LOCATION = path.join('/');
        }

        if (port !== 843) {
          WebSocket.loadFlashPolicyFile('xmlsocket://' + options.host + ':' + port);
        }

        WebSocket.__initialize();
        Flashsocket.loaded = true;
      }

      fn.call(self);
    }

    var self = this;
    if (document.body) return init();

    io.util.load(init);
  };

  /**
   * Check if the FlashSocket transport is supported as it requires that the Adobe
   * Flash Player plug-in version `10.0.0` or greater is installed. And also check if
   * the polyfill is correctly loaded.
   *
   * @returns {Boolean}
   * @api public
   */

  Flashsocket.check = function () {
    if (
        typeof WebSocket == 'undefined'
      || !('__initialize' in WebSocket) || !swfobject
    ) return false;

    return swfobject.getFlashPlayerVersion().major >= 10;
  };

  /**
   * Check if the FlashSocket transport can be used as cross domain / cross origin 
   * transport. Because we can't see which type (secure or insecure) of .swf is used
   * we will just return true.
   *
   * @returns {Boolean}
   * @api public
   */

  Flashsocket.xdomainCheck = function () {
    return true;
  };

  /**
   * Disable AUTO_INITIALIZATION
   */

  if (typeof window != 'undefined') {
    WEB_SOCKET_DISABLE_AUTO_INITIALIZATION = true;
  }

  /**
   * Add the transport to your public io.transports array.
   *
   * @api private
   */

  io.transports.push('flashsocket');
})(
    'undefined' != typeof io ? io.Transport : module.exports
  , 'undefined' != typeof io ? io : module.parent.exports
);
/*	SWFObject v2.2 <http://code.google.com/p/swfobject/> 
	is released under the MIT License <http://www.opensource.org/licenses/mit-license.php> 
*/
if ('undefined' != typeof window) {
var swfobject=function(){var D="undefined",r="object",S="Shockwave Flash",W="ShockwaveFlash.ShockwaveFlash",q="application/x-shockwave-flash",R="SWFObjectExprInst",x="onreadystatechange",O=window,j=document,t=navigator,T=false,U=[h],o=[],N=[],I=[],l,Q,E,B,J=false,a=false,n,G,m=true,M=function(){var aa=typeof j.getElementById!=D&&typeof j.getElementsByTagName!=D&&typeof j.createElement!=D,ah=t.userAgent.toLowerCase(),Y=t.platform.toLowerCase(),ae=Y?/win/.test(Y):/win/.test(ah),ac=Y?/mac/.test(Y):/mac/.test(ah),af=/webkit/.test(ah)?parseFloat(ah.replace(/^.*webkit\/(\d+(\.\d+)?).*$/,"$1")):false,X=!+"\v1",ag=[0,0,0],ab=null;if(typeof t.plugins!=D&&typeof t.plugins[S]==r){ab=t.plugins[S].description;if(ab&&!(typeof t.mimeTypes!=D&&t.mimeTypes[q]&&!t.mimeTypes[q].enabledPlugin)){T=true;X=false;ab=ab.replace(/^.*\s+(\S+\s+\S+$)/,"$1");ag[0]=parseInt(ab.replace(/^(.*)\..*$/,"$1"),10);ag[1]=parseInt(ab.replace(/^.*\.(.*)\s.*$/,"$1"),10);ag[2]=/[a-zA-Z]/.test(ab)?parseInt(ab.replace(/^.*[a-zA-Z]+(.*)$/,"$1"),10):0}}else{if(typeof O[(['Active'].concat('Object').join('X'))]!=D){try{var ad=new window[(['Active'].concat('Object').join('X'))](W);if(ad){ab=ad.GetVariable("$version");if(ab){X=true;ab=ab.split(" ")[1].split(",");ag=[parseInt(ab[0],10),parseInt(ab[1],10),parseInt(ab[2],10)]}}}catch(Z){}}}return{w3:aa,pv:ag,wk:af,ie:X,win:ae,mac:ac}}(),k=function(){if(!M.w3){return}if((typeof j.readyState!=D&&j.readyState=="complete")||(typeof j.readyState==D&&(j.getElementsByTagName("body")[0]||j.body))){f()}if(!J){if(typeof j.addEventListener!=D){j.addEventListener("DOMContentLoaded",f,false)}if(M.ie&&M.win){j.attachEvent(x,function(){if(j.readyState=="complete"){j.detachEvent(x,arguments.callee);f()}});if(O==top){(function(){if(J){return}try{j.documentElement.doScroll("left")}catch(X){setTimeout(arguments.callee,0);return}f()})()}}if(M.wk){(function(){if(J){return}if(!/loaded|complete/.test(j.readyState)){setTimeout(arguments.callee,0);return}f()})()}s(f)}}();function f(){if(J){return}try{var Z=j.getElementsByTagName("body")[0].appendChild(C("span"));Z.parentNode.removeChild(Z)}catch(aa){return}J=true;var X=U.length;for(var Y=0;Y<X;Y++){U[Y]()}}function K(X){if(J){X()}else{U[U.length]=X}}function s(Y){if(typeof O.addEventListener!=D){O.addEventListener("load",Y,false)}else{if(typeof j.addEventListener!=D){j.addEventListener("load",Y,false)}else{if(typeof O.attachEvent!=D){i(O,"onload",Y)}else{if(typeof O.onload=="function"){var X=O.onload;O.onload=function(){X();Y()}}else{O.onload=Y}}}}}function h(){if(T){V()}else{H()}}function V(){var X=j.getElementsByTagName("body")[0];var aa=C(r);aa.setAttribute("type",q);var Z=X.appendChild(aa);if(Z){var Y=0;(function(){if(typeof Z.GetVariable!=D){var ab=Z.GetVariable("$version");if(ab){ab=ab.split(" ")[1].split(",");M.pv=[parseInt(ab[0],10),parseInt(ab[1],10),parseInt(ab[2],10)]}}else{if(Y<10){Y++;setTimeout(arguments.callee,10);return}}X.removeChild(aa);Z=null;H()})()}else{H()}}function H(){var ag=o.length;if(ag>0){for(var af=0;af<ag;af++){var Y=o[af].id;var ab=o[af].callbackFn;var aa={success:false,id:Y};if(M.pv[0]>0){var ae=c(Y);if(ae){if(F(o[af].swfVersion)&&!(M.wk&&M.wk<312)){w(Y,true);if(ab){aa.success=true;aa.ref=z(Y);ab(aa)}}else{if(o[af].expressInstall&&A()){var ai={};ai.data=o[af].expressInstall;ai.width=ae.getAttribute("width")||"0";ai.height=ae.getAttribute("height")||"0";if(ae.getAttribute("class")){ai.styleclass=ae.getAttribute("class")}if(ae.getAttribute("align")){ai.align=ae.getAttribute("align")}var ah={};var X=ae.getElementsByTagName("param");var ac=X.length;for(var ad=0;ad<ac;ad++){if(X[ad].getAttribute("name").toLowerCase()!="movie"){ah[X[ad].getAttribute("name")]=X[ad].getAttribute("value")}}P(ai,ah,Y,ab)}else{p(ae);if(ab){ab(aa)}}}}}else{w(Y,true);if(ab){var Z=z(Y);if(Z&&typeof Z.SetVariable!=D){aa.success=true;aa.ref=Z}ab(aa)}}}}}function z(aa){var X=null;var Y=c(aa);if(Y&&Y.nodeName=="OBJECT"){if(typeof Y.SetVariable!=D){X=Y}else{var Z=Y.getElementsByTagName(r)[0];if(Z){X=Z}}}return X}function A(){return !a&&F("6.0.65")&&(M.win||M.mac)&&!(M.wk&&M.wk<312)}function P(aa,ab,X,Z){a=true;E=Z||null;B={success:false,id:X};var ae=c(X);if(ae){if(ae.nodeName=="OBJECT"){l=g(ae);Q=null}else{l=ae;Q=X}aa.id=R;if(typeof aa.width==D||(!/%$/.test(aa.width)&&parseInt(aa.width,10)<310)){aa.width="310"}if(typeof aa.height==D||(!/%$/.test(aa.height)&&parseInt(aa.height,10)<137)){aa.height="137"}j.title=j.title.slice(0,47)+" - Flash Player Installation";var ad=M.ie&&M.win?(['Active'].concat('').join('X')):"PlugIn",ac="MMredirectURL="+O.location.toString().replace(/&/g,"%26")+"&MMplayerType="+ad+"&MMdoctitle="+j.title;if(typeof ab.flashvars!=D){ab.flashvars+="&"+ac}else{ab.flashvars=ac}if(M.ie&&M.win&&ae.readyState!=4){var Y=C("div");X+="SWFObjectNew";Y.setAttribute("id",X);ae.parentNode.insertBefore(Y,ae);ae.style.display="none";(function(){if(ae.readyState==4){ae.parentNode.removeChild(ae)}else{setTimeout(arguments.callee,10)}})()}u(aa,ab,X)}}function p(Y){if(M.ie&&M.win&&Y.readyState!=4){var X=C("div");Y.parentNode.insertBefore(X,Y);X.parentNode.replaceChild(g(Y),X);Y.style.display="none";(function(){if(Y.readyState==4){Y.parentNode.removeChild(Y)}else{setTimeout(arguments.callee,10)}})()}else{Y.parentNode.replaceChild(g(Y),Y)}}function g(ab){var aa=C("div");if(M.win&&M.ie){aa.innerHTML=ab.innerHTML}else{var Y=ab.getElementsByTagName(r)[0];if(Y){var ad=Y.childNodes;if(ad){var X=ad.length;for(var Z=0;Z<X;Z++){if(!(ad[Z].nodeType==1&&ad[Z].nodeName=="PARAM")&&!(ad[Z].nodeType==8)){aa.appendChild(ad[Z].cloneNode(true))}}}}}return aa}function u(ai,ag,Y){var X,aa=c(Y);if(M.wk&&M.wk<312){return X}if(aa){if(typeof ai.id==D){ai.id=Y}if(M.ie&&M.win){var ah="";for(var ae in ai){if(ai[ae]!=Object.prototype[ae]){if(ae.toLowerCase()=="data"){ag.movie=ai[ae]}else{if(ae.toLowerCase()=="styleclass"){ah+=' class="'+ai[ae]+'"'}else{if(ae.toLowerCase()!="classid"){ah+=" "+ae+'="'+ai[ae]+'"'}}}}}var af="";for(var ad in ag){if(ag[ad]!=Object.prototype[ad]){af+='<param name="'+ad+'" value="'+ag[ad]+'" />'}}aa.outerHTML='<object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000"'+ah+">"+af+"</object>";N[N.length]=ai.id;X=c(ai.id)}else{var Z=C(r);Z.setAttribute("type",q);for(var ac in ai){if(ai[ac]!=Object.prototype[ac]){if(ac.toLowerCase()=="styleclass"){Z.setAttribute("class",ai[ac])}else{if(ac.toLowerCase()!="classid"){Z.setAttribute(ac,ai[ac])}}}}for(var ab in ag){if(ag[ab]!=Object.prototype[ab]&&ab.toLowerCase()!="movie"){e(Z,ab,ag[ab])}}aa.parentNode.replaceChild(Z,aa);X=Z}}return X}function e(Z,X,Y){var aa=C("param");aa.setAttribute("name",X);aa.setAttribute("value",Y);Z.appendChild(aa)}function y(Y){var X=c(Y);if(X&&X.nodeName=="OBJECT"){if(M.ie&&M.win){X.style.display="none";(function(){if(X.readyState==4){b(Y)}else{setTimeout(arguments.callee,10)}})()}else{X.parentNode.removeChild(X)}}}function b(Z){var Y=c(Z);if(Y){for(var X in Y){if(typeof Y[X]=="function"){Y[X]=null}}Y.parentNode.removeChild(Y)}}function c(Z){var X=null;try{X=j.getElementById(Z)}catch(Y){}return X}function C(X){return j.createElement(X)}function i(Z,X,Y){Z.attachEvent(X,Y);I[I.length]=[Z,X,Y]}function F(Z){var Y=M.pv,X=Z.split(".");X[0]=parseInt(X[0],10);X[1]=parseInt(X[1],10)||0;X[2]=parseInt(X[2],10)||0;return(Y[0]>X[0]||(Y[0]==X[0]&&Y[1]>X[1])||(Y[0]==X[0]&&Y[1]==X[1]&&Y[2]>=X[2]))?true:false}function v(ac,Y,ad,ab){if(M.ie&&M.mac){return}var aa=j.getElementsByTagName("head")[0];if(!aa){return}var X=(ad&&typeof ad=="string")?ad:"screen";if(ab){n=null;G=null}if(!n||G!=X){var Z=C("style");Z.setAttribute("type","text/css");Z.setAttribute("media",X);n=aa.appendChild(Z);if(M.ie&&M.win&&typeof j.styleSheets!=D&&j.styleSheets.length>0){n=j.styleSheets[j.styleSheets.length-1]}G=X}if(M.ie&&M.win){if(n&&typeof n.addRule==r){n.addRule(ac,Y)}}else{if(n&&typeof j.createTextNode!=D){n.appendChild(j.createTextNode(ac+" {"+Y+"}"))}}}function w(Z,X){if(!m){return}var Y=X?"visible":"hidden";if(J&&c(Z)){c(Z).style.visibility=Y}else{v("#"+Z,"visibility:"+Y)}}function L(Y){var Z=/[\\\"<>\.;]/;var X=Z.exec(Y)!=null;return X&&typeof encodeURIComponent!=D?encodeURIComponent(Y):Y}var d=function(){if(M.ie&&M.win){window.attachEvent("onunload",function(){var ac=I.length;for(var ab=0;ab<ac;ab++){I[ab][0].detachEvent(I[ab][1],I[ab][2])}var Z=N.length;for(var aa=0;aa<Z;aa++){y(N[aa])}for(var Y in M){M[Y]=null}M=null;for(var X in swfobject){swfobject[X]=null}swfobject=null})}}();return{registerObject:function(ab,X,aa,Z){if(M.w3&&ab&&X){var Y={};Y.id=ab;Y.swfVersion=X;Y.expressInstall=aa;Y.callbackFn=Z;o[o.length]=Y;w(ab,false)}else{if(Z){Z({success:false,id:ab})}}},getObjectById:function(X){if(M.w3){return z(X)}},embedSWF:function(ab,ah,ae,ag,Y,aa,Z,ad,af,ac){var X={success:false,id:ah};if(M.w3&&!(M.wk&&M.wk<312)&&ab&&ah&&ae&&ag&&Y){w(ah,false);K(function(){ae+="";ag+="";var aj={};if(af&&typeof af===r){for(var al in af){aj[al]=af[al]}}aj.data=ab;aj.width=ae;aj.height=ag;var am={};if(ad&&typeof ad===r){for(var ak in ad){am[ak]=ad[ak]}}if(Z&&typeof Z===r){for(var ai in Z){if(typeof am.flashvars!=D){am.flashvars+="&"+ai+"="+Z[ai]}else{am.flashvars=ai+"="+Z[ai]}}}if(F(Y)){var an=u(aj,am,ah);if(aj.id==ah){w(ah,true)}X.success=true;X.ref=an}else{if(aa&&A()){aj.data=aa;P(aj,am,ah,ac);return}else{w(ah,true)}}if(ac){ac(X)}})}else{if(ac){ac(X)}}},switchOffAutoHideShow:function(){m=false},ua:M,getFlashPlayerVersion:function(){return{major:M.pv[0],minor:M.pv[1],release:M.pv[2]}},hasFlashPlayerVersion:F,createSWF:function(Z,Y,X){if(M.w3){return u(Z,Y,X)}else{return undefined}},showExpressInstall:function(Z,aa,X,Y){if(M.w3&&A()){P(Z,aa,X,Y)}},removeSWF:function(X){if(M.w3){y(X)}},createCSS:function(aa,Z,Y,X){if(M.w3){v(aa,Z,Y,X)}},addDomLoadEvent:K,addLoadEvent:s,getQueryParamValue:function(aa){var Z=j.location.search||j.location.hash;if(Z){if(/\?/.test(Z)){Z=Z.split("?")[1]}if(aa==null){return L(Z)}var Y=Z.split("&");for(var X=0;X<Y.length;X++){if(Y[X].substring(0,Y[X].indexOf("="))==aa){return L(Y[X].substring((Y[X].indexOf("=")+1)))}}}return""},expressInstallCallback:function(){if(a){var X=c(R);if(X&&l){X.parentNode.replaceChild(l,X);if(Q){w(Q,true);if(M.ie&&M.win){l.style.display="block"}}if(E){E(B)}}a=false}}}}();
}
// Copyright: Hiroshi Ichikawa <http://gimite.net/en/>
// License: New BSD License
// Reference: http://dev.w3.org/html5/websockets/
// Reference: http://tools.ietf.org/html/draft-hixie-thewebsocketprotocol

(function() {
  
  if ('undefined' == typeof window || window.WebSocket) return;

  var console = window.console;
  if (!console || !console.log || !console.error) {
    console = {log: function(){ }, error: function(){ }};
  }
  
  if (!swfobject.hasFlashPlayerVersion("10.0.0")) {
    console.error("Flash Player >= 10.0.0 is required.");
    return;
  }
  if (location.protocol == "file:") {
    console.error(
      "WARNING: web-socket-js doesn't work in file:///... URL " +
      "unless you set Flash Security Settings properly. " +
      "Open the page via Web server i.e. http://...");
  }

  /**
   * This class represents a faux web socket.
   * @param {string} url
   * @param {array or string} protocols
   * @param {string} proxyHost
   * @param {int} proxyPort
   * @param {string} headers
   */
  WebSocket = function(url, protocols, proxyHost, proxyPort, headers) {
    var self = this;
    self.__id = WebSocket.__nextId++;
    WebSocket.__instances[self.__id] = self;
    self.readyState = WebSocket.CONNECTING;
    self.bufferedAmount = 0;
    self.__events = {};
    if (!protocols) {
      protocols = [];
    } else if (typeof protocols == "string") {
      protocols = [protocols];
    }
    // Uses setTimeout() to make sure __createFlash() runs after the caller sets ws.onopen etc.
    // Otherwise, when onopen fires immediately, onopen is called before it is set.
    setTimeout(function() {
      WebSocket.__addTask(function() {
        WebSocket.__flash.create(
            self.__id, url, protocols, proxyHost || null, proxyPort || 0, headers || null);
      });
    }, 0);
  };

  /**
   * Send data to the web socket.
   * @param {string} data  The data to send to the socket.
   * @return {boolean}  True for success, false for failure.
   */
  WebSocket.prototype.send = function(data) {
    if (this.readyState == WebSocket.CONNECTING) {
      throw "INVALID_STATE_ERR: Web Socket connection has not been established";
    }
    // We use encodeURIComponent() here, because FABridge doesn't work if
    // the argument includes some characters. We don't use escape() here
    // because of this:
    // https://developer.mozilla.org/en/Core_JavaScript_1.5_Guide/Functions#escape_and_unescape_Functions
    // But it looks decodeURIComponent(encodeURIComponent(s)) doesn't
    // preserve all Unicode characters either e.g. "\uffff" in Firefox.
    // Note by wtritch: Hopefully this will not be necessary using ExternalInterface.  Will require
    // additional testing.
    var result = WebSocket.__flash.send(this.__id, encodeURIComponent(data));
    if (result < 0) { // success
      return true;
    } else {
      this.bufferedAmount += result;
      return false;
    }
  };

  /**
   * Close this web socket gracefully.
   */
  WebSocket.prototype.close = function() {
    if (this.readyState == WebSocket.CLOSED || this.readyState == WebSocket.CLOSING) {
      return;
    }
    this.readyState = WebSocket.CLOSING;
    WebSocket.__flash.close(this.__id);
  };

  /**
   * Implementation of {@link <a href="http://www.w3.org/TR/DOM-Level-2-Events/events.html#Events-registration">DOM 2 EventTarget Interface</a>}
   *
   * @param {string} type
   * @param {function} listener
   * @param {boolean} useCapture
   * @return void
   */
  WebSocket.prototype.addEventListener = function(type, listener, useCapture) {
    if (!(type in this.__events)) {
      this.__events[type] = [];
    }
    this.__events[type].push(listener);
  };

  /**
   * Implementation of {@link <a href="http://www.w3.org/TR/DOM-Level-2-Events/events.html#Events-registration">DOM 2 EventTarget Interface</a>}
   *
   * @param {string} type
   * @param {function} listener
   * @param {boolean} useCapture
   * @return void
   */
  WebSocket.prototype.removeEventListener = function(type, listener, useCapture) {
    if (!(type in this.__events)) return;
    var events = this.__events[type];
    for (var i = events.length - 1; i >= 0; --i) {
      if (events[i] === listener) {
        events.splice(i, 1);
        break;
      }
    }
  };

  /**
   * Implementation of {@link <a href="http://www.w3.org/TR/DOM-Level-2-Events/events.html#Events-registration">DOM 2 EventTarget Interface</a>}
   *
   * @param {Event} event
   * @return void
   */
  WebSocket.prototype.dispatchEvent = function(event) {
    var events = this.__events[event.type] || [];
    for (var i = 0; i < events.length; ++i) {
      events[i](event);
    }
    var handler = this["on" + event.type];
    if (handler) handler(event);
  };

  /**
   * Handles an event from Flash.
   * @param {Object} flashEvent
   */
  WebSocket.prototype.__handleEvent = function(flashEvent) {
    if ("readyState" in flashEvent) {
      this.readyState = flashEvent.readyState;
    }
    if ("protocol" in flashEvent) {
      this.protocol = flashEvent.protocol;
    }
    
    var jsEvent;
    if (flashEvent.type == "open" || flashEvent.type == "error") {
      jsEvent = this.__createSimpleEvent(flashEvent.type);
    } else if (flashEvent.type == "close") {
      // TODO implement jsEvent.wasClean
      jsEvent = this.__createSimpleEvent("close");
    } else if (flashEvent.type == "message") {
      var data = decodeURIComponent(flashEvent.message);
      jsEvent = this.__createMessageEvent("message", data);
    } else {
      throw "unknown event type: " + flashEvent.type;
    }
    
    this.dispatchEvent(jsEvent);
  };
  
  WebSocket.prototype.__createSimpleEvent = function(type) {
    if (document.createEvent && window.Event) {
      var event = document.createEvent("Event");
      event.initEvent(type, false, false);
      return event;
    } else {
      return {type: type, bubbles: false, cancelable: false};
    }
  };
  
  WebSocket.prototype.__createMessageEvent = function(type, data) {
    if (document.createEvent && window.MessageEvent && !window.opera) {
      var event = document.createEvent("MessageEvent");
      event.initMessageEvent("message", false, false, data, null, null, window, null);
      return event;
    } else {
      // IE and Opera, the latter one truncates the data parameter after any 0x00 bytes.
      return {type: type, data: data, bubbles: false, cancelable: false};
    }
  };
  
  /**
   * Define the WebSocket readyState enumeration.
   */
  WebSocket.CONNECTING = 0;
  WebSocket.OPEN = 1;
  WebSocket.CLOSING = 2;
  WebSocket.CLOSED = 3;

  WebSocket.__flash = null;
  WebSocket.__instances = {};
  WebSocket.__tasks = [];
  WebSocket.__nextId = 0;
  
  /**
   * Load a new flash security policy file.
   * @param {string} url
   */
  WebSocket.loadFlashPolicyFile = function(url){
    WebSocket.__addTask(function() {
      WebSocket.__flash.loadManualPolicyFile(url);
    });
  };

  /**
   * Loads WebSocketMain.swf and creates WebSocketMain object in Flash.
   */
  WebSocket.__initialize = function() {
    if (WebSocket.__flash) return;
    
    if (WebSocket.__swfLocation) {
      // For backword compatibility.
      window.WEB_SOCKET_SWF_LOCATION = WebSocket.__swfLocation;
    }
    if (!window.WEB_SOCKET_SWF_LOCATION) {
      console.error("[WebSocket] set WEB_SOCKET_SWF_LOCATION to location of WebSocketMain.swf");
      return;
    }
    var container = document.createElement("div");
    container.id = "webSocketContainer";
    // Hides Flash box. We cannot use display: none or visibility: hidden because it prevents
    // Flash from loading at least in IE. So we move it out of the screen at (-100, -100).
    // But this even doesn't work with Flash Lite (e.g. in Droid Incredible). So with Flash
    // Lite, we put it at (0, 0). This shows 1x1 box visible at left-top corner but this is
    // the best we can do as far as we know now.
    container.style.position = "absolute";
    if (WebSocket.__isFlashLite()) {
      container.style.left = "0px";
      container.style.top = "0px";
    } else {
      container.style.left = "-100px";
      container.style.top = "-100px";
    }
    var holder = document.createElement("div");
    holder.id = "webSocketFlash";
    container.appendChild(holder);
    document.body.appendChild(container);
    // See this article for hasPriority:
    // http://help.adobe.com/en_US/as3/mobile/WS4bebcd66a74275c36cfb8137124318eebc6-7ffd.html
    swfobject.embedSWF(
      WEB_SOCKET_SWF_LOCATION,
      "webSocketFlash",
      "1" /* width */,
      "1" /* height */,
      "10.0.0" /* SWF version */,
      null,
      null,
      {hasPriority: true, swliveconnect : true, allowScriptAccess: "always"},
      null,
      function(e) {
        if (!e.success) {
          console.error("[WebSocket] swfobject.embedSWF failed");
        }
      });
  };
  
  /**
   * Called by Flash to notify JS that it's fully loaded and ready
   * for communication.
   */
  WebSocket.__onFlashInitialized = function() {
    // We need to set a timeout here to avoid round-trip calls
    // to flash during the initialization process.
    setTimeout(function() {
      WebSocket.__flash = document.getElementById("webSocketFlash");
      WebSocket.__flash.setCallerUrl(location.href);
      WebSocket.__flash.setDebug(!!window.WEB_SOCKET_DEBUG);
      for (var i = 0; i < WebSocket.__tasks.length; ++i) {
        WebSocket.__tasks[i]();
      }
      WebSocket.__tasks = [];
    }, 0);
  };
  
  /**
   * Called by Flash to notify WebSockets events are fired.
   */
  WebSocket.__onFlashEvent = function() {
    setTimeout(function() {
      try {
        // Gets events using receiveEvents() instead of getting it from event object
        // of Flash event. This is to make sure to keep message order.
        // It seems sometimes Flash events don't arrive in the same order as they are sent.
        var events = WebSocket.__flash.receiveEvents();
        for (var i = 0; i < events.length; ++i) {
          WebSocket.__instances[events[i].webSocketId].__handleEvent(events[i]);
        }
      } catch (e) {
        console.error(e);
      }
    }, 0);
    return true;
  };
  
  // Called by Flash.
  WebSocket.__log = function(message) {
    console.log(decodeURIComponent(message));
  };
  
  // Called by Flash.
  WebSocket.__error = function(message) {
    console.error(decodeURIComponent(message));
  };
  
  WebSocket.__addTask = function(task) {
    if (WebSocket.__flash) {
      task();
    } else {
      WebSocket.__tasks.push(task);
    }
  };
  
  /**
   * Test if the browser is running flash lite.
   * @return {boolean} True if flash lite is running, false otherwise.
   */
  WebSocket.__isFlashLite = function() {
    if (!window.navigator || !window.navigator.mimeTypes) {
      return false;
    }
    var mimeType = window.navigator.mimeTypes["application/x-shockwave-flash"];
    if (!mimeType || !mimeType.enabledPlugin || !mimeType.enabledPlugin.filename) {
      return false;
    }
    return mimeType.enabledPlugin.filename.match(/flashlite/i) ? true : false;
  };
  
  if (!window.WEB_SOCKET_DISABLE_AUTO_INITIALIZATION) {
    if (window.addEventListener) {
      window.addEventListener("load", function(){
        WebSocket.__initialize();
      }, false);
    } else {
      window.attachEvent("onload", function(){
        WebSocket.__initialize();
      });
    }
  }
  
})();

/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, io, global) {

  /**
   * Expose constructor.
   *
   * @api public
   */

  exports.XHR = XHR;

  /**
   * XHR constructor
   *
   * @costructor
   * @api public
   */

  function XHR (socket) {
    if (!socket) return;

    io.Transport.apply(this, arguments);
    this.sendBuffer = [];
  };

  /**
   * Inherits from Transport.
   */

  io.util.inherit(XHR, io.Transport);

  /**
   * Establish a connection
   *
   * @returns {Transport}
   * @api public
   */

  XHR.prototype.open = function () {
    this.socket.setBuffer(false);
    this.onOpen();
    this.get();

    // we need to make sure the request succeeds since we have no indication
    // whether the request opened or not until it succeeded.
    this.setCloseTimeout();

    return this;
  };

  /**
   * Check if we need to send data to the Socket.IO server, if we have data in our
   * buffer we encode it and forward it to the `post` method.
   *
   * @api private
   */

  XHR.prototype.payload = function (payload) {
    var msgs = [];

    for (var i = 0, l = payload.length; i < l; i++) {
      msgs.push(io.parser.encodePacket(payload[i]));
    }

    this.send(io.parser.encodePayload(msgs));
  };

  /**
   * Send data to the Socket.IO server.
   *
   * @param data The message
   * @returns {Transport}
   * @api public
   */

  XHR.prototype.send = function (data) {
    this.post(data);
    return this;
  };

  /**
   * Posts a encoded message to the Socket.IO server.
   *
   * @param {String} data A encoded message.
   * @api private
   */

  function empty () { };

  XHR.prototype.post = function (data) {
    var self = this;
    this.socket.setBuffer(true);

    function stateChange () {
      if (this.readyState == 4) {
        this.onreadystatechange = empty;
        self.posting = false;

        if (this.status == 200){
          self.socket.setBuffer(false);
        } else {
          self.onClose();
        }
      }
    }

    function onload () {
      this.onload = empty;
      self.socket.setBuffer(false);
    };

    this.sendXHR = this.request('POST');

    if (global.XDomainRequest && this.sendXHR instanceof XDomainRequest) {
      this.sendXHR.onload = this.sendXHR.onerror = onload;
    } else {
      this.sendXHR.onreadystatechange = stateChange;
    }

    this.sendXHR.send(data);
  };

  /**
   * Disconnects the established `XHR` connection.
   *
   * @returns {Transport}
   * @api public
   */

  XHR.prototype.close = function () {
    this.onClose();
    return this;
  };

  /**
   * Generates a configured XHR request
   *
   * @param {String} url The url that needs to be requested.
   * @param {String} method The method the request should use.
   * @returns {XMLHttpRequest}
   * @api private
   */

  XHR.prototype.request = function (method) {
    var req = io.util.request(this.socket.isXDomain())
      , query = io.util.query(this.socket.options.query, 't=' + +new Date);

    req.open(method || 'GET', this.prepareUrl() + query, true);

    if (method == 'POST') {
      try {
        if (req.setRequestHeader) {
          req.setRequestHeader('Content-type', 'text/plain;charset=UTF-8');
        } else {
          // XDomainRequest
          req.contentType = 'text/plain';
        }
      } catch (e) {}
    }

    return req;
  };

  /**
   * Returns the scheme to use for the transport URLs.
   *
   * @api private
   */

  XHR.prototype.scheme = function () {
    return this.socket.options.secure ? 'https' : 'http';
  };

  /**
   * Check if the XHR transports are supported
   *
   * @param {Boolean} xdomain Check if we support cross domain requests.
   * @returns {Boolean}
   * @api public
   */

  XHR.check = function (socket, xdomain) {
    try {
      var request = io.util.request(xdomain),
          usesXDomReq = (global.XDomainRequest && request instanceof XDomainRequest),
          socketProtocol = (socket && socket.options && socket.options.secure ? 'https:' : 'http:'),
          isXProtocol = (global.location && socketProtocol != global.location.protocol);
      if (request && !(usesXDomReq && isXProtocol)) {
        return true;
      }
    } catch(e) {}

    return false;
  };

  /**
   * Check if the XHR transport supports cross domain requests.
   *
   * @returns {Boolean}
   * @api public
   */

  XHR.xdomainCheck = function (socket) {
    return XHR.check(socket, true);
  };

})(
    'undefined' != typeof io ? io.Transport : module.exports
  , 'undefined' != typeof io ? io : module.parent.exports
  , this
);
/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, io) {

  /**
   * Expose constructor.
   */

  exports.htmlfile = HTMLFile;

  /**
   * The HTMLFile transport creates a `forever iframe` based transport
   * for Internet Explorer. Regular forever iframe implementations will 
   * continuously trigger the browsers buzy indicators. If the forever iframe
   * is created inside a `htmlfile` these indicators will not be trigged.
   *
   * @constructor
   * @extends {io.Transport.XHR}
   * @api public
   */

  function HTMLFile (socket) {
    io.Transport.XHR.apply(this, arguments);
  };

  /**
   * Inherits from XHR transport.
   */

  io.util.inherit(HTMLFile, io.Transport.XHR);

  /**
   * Transport name
   *
   * @api public
   */

  HTMLFile.prototype.name = 'htmlfile';

  /**
   * Creates a new Ac...eX `htmlfile` with a forever loading iframe
   * that can be used to listen to messages. Inside the generated
   * `htmlfile` a reference will be made to the HTMLFile transport.
   *
   * @api private
   */

  HTMLFile.prototype.get = function () {
    this.doc = new window[(['Active'].concat('Object').join('X'))]('htmlfile');
    this.doc.open();
    this.doc.write('<html></html>');
    this.doc.close();
    this.doc.parentWindow.s = this;

    var iframeC = this.doc.createElement('div');
    iframeC.className = 'socketio';

    this.doc.body.appendChild(iframeC);
    this.iframe = this.doc.createElement('iframe');

    iframeC.appendChild(this.iframe);

    var self = this
      , query = io.util.query(this.socket.options.query, 't='+ +new Date);

    this.iframe.src = this.prepareUrl() + query;

    io.util.on(window, 'unload', function () {
      self.destroy();
    });
  };

  /**
   * The Socket.IO server will write script tags inside the forever
   * iframe, this function will be used as callback for the incoming
   * information.
   *
   * @param {String} data The message
   * @param {document} doc Reference to the context
   * @api private
   */

  HTMLFile.prototype._ = function (data, doc) {
    // unescape all forward slashes. see GH-1251
    data = data.replace(/\\\//g, '/');
    this.onData(data);
    try {
      var script = doc.getElementsByTagName('script')[0];
      script.parentNode.removeChild(script);
    } catch (e) { }
  };

  /**
   * Destroy the established connection, iframe and `htmlfile`.
   * And calls the `CollectGarbage` function of Internet Explorer
   * to release the memory.
   *
   * @api private
   */

  HTMLFile.prototype.destroy = function () {
    if (this.iframe){
      try {
        this.iframe.src = 'about:blank';
      } catch(e){}

      this.doc = null;
      this.iframe.parentNode.removeChild(this.iframe);
      this.iframe = null;

      CollectGarbage();
    }
  };

  /**
   * Disconnects the established connection.
   *
   * @returns {Transport} Chaining.
   * @api public
   */

  HTMLFile.prototype.close = function () {
    this.destroy();
    return io.Transport.XHR.prototype.close.call(this);
  };

  /**
   * Checks if the browser supports this transport. The browser
   * must have an `Ac...eXObject` implementation.
   *
   * @return {Boolean}
   * @api public
   */

  HTMLFile.check = function (socket) {
    if (typeof window != "undefined" && (['Active'].concat('Object').join('X')) in window){
      try {
        var a = new window[(['Active'].concat('Object').join('X'))]('htmlfile');
        return a && io.Transport.XHR.check(socket);
      } catch(e){}
    }
    return false;
  };

  /**
   * Check if cross domain requests are supported.
   *
   * @returns {Boolean}
   * @api public
   */

  HTMLFile.xdomainCheck = function () {
    // we can probably do handling for sub-domains, we should
    // test that it's cross domain but a subdomain here
    return false;
  };

  /**
   * Add the transport to your public io.transports array.
   *
   * @api private
   */

  io.transports.push('htmlfile');

})(
    'undefined' != typeof io ? io.Transport : module.exports
  , 'undefined' != typeof io ? io : module.parent.exports
);

/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, io, global) {

  /**
   * Expose constructor.
   */

  exports['xhr-polling'] = XHRPolling;

  /**
   * The XHR-polling transport uses long polling XHR requests to create a
   * "persistent" connection with the server.
   *
   * @constructor
   * @api public
   */

  function XHRPolling () {
    io.Transport.XHR.apply(this, arguments);
  };

  /**
   * Inherits from XHR transport.
   */

  io.util.inherit(XHRPolling, io.Transport.XHR);

  /**
   * Merge the properties from XHR transport
   */

  io.util.merge(XHRPolling, io.Transport.XHR);

  /**
   * Transport name
   *
   * @api public
   */

  XHRPolling.prototype.name = 'xhr-polling';

  /**
   * Indicates whether heartbeats is enabled for this transport
   *
   * @api private
   */

  XHRPolling.prototype.heartbeats = function () {
    return false;
  };

  /** 
   * Establish a connection, for iPhone and Android this will be done once the page
   * is loaded.
   *
   * @returns {Transport} Chaining.
   * @api public
   */

  XHRPolling.prototype.open = function () {
    var self = this;

    io.Transport.XHR.prototype.open.call(self);
    return false;
  };

  /**
   * Starts a XHR request to wait for incoming messages.
   *
   * @api private
   */

  function empty () {};

  XHRPolling.prototype.get = function () {
    if (!this.isOpen) return;

    var self = this;

    function stateChange () {
      if (this.readyState == 4) {
        this.onreadystatechange = empty;

        if (this.status == 200) {
          self.onData(this.responseText);
          self.get();
        } else {
          self.onClose();
        }
      }
    };

    function onload () {
      this.onload = empty;
      this.onerror = empty;
      self.retryCounter = 1;
      self.onData(this.responseText);
      self.get();
    };

    function onerror () {
      self.retryCounter ++;
      if(!self.retryCounter || self.retryCounter > 3) {
        self.onClose();  
      } else {
        self.get();
      }
    };

    this.xhr = this.request();

    if (global.XDomainRequest && this.xhr instanceof XDomainRequest) {
      this.xhr.onload = onload;
      this.xhr.onerror = onerror;
    } else {
      this.xhr.onreadystatechange = stateChange;
    }

    this.xhr.send(null);
  };

  /**
   * Handle the unclean close behavior.
   *
   * @api private
   */

  XHRPolling.prototype.onClose = function () {
    io.Transport.XHR.prototype.onClose.call(this);

    if (this.xhr) {
      this.xhr.onreadystatechange = this.xhr.onload = this.xhr.onerror = empty;
      try {
        this.xhr.abort();
      } catch(e){}
      this.xhr = null;
    }
  };

  /**
   * Webkit based browsers show a infinit spinner when you start a XHR request
   * before the browsers onload event is called so we need to defer opening of
   * the transport until the onload event is called. Wrapping the cb in our
   * defer method solve this.
   *
   * @param {Socket} socket The socket instance that needs a transport
   * @param {Function} fn The callback
   * @api private
   */

  XHRPolling.prototype.ready = function (socket, fn) {
    var self = this;

    io.util.defer(function () {
      fn.call(self);
    });
  };

  /**
   * Add the transport to your public io.transports array.
   *
   * @api private
   */

  io.transports.push('xhr-polling');

})(
    'undefined' != typeof io ? io.Transport : module.exports
  , 'undefined' != typeof io ? io : module.parent.exports
  , this
);

/**
 * socket.io
 * Copyright(c) 2011 LearnBoost <dev@learnboost.com>
 * MIT Licensed
 */

(function (exports, io, global) {
  /**
   * There is a way to hide the loading indicator in Firefox. If you create and
   * remove a iframe it will stop showing the current loading indicator.
   * Unfortunately we can't feature detect that and UA sniffing is evil.
   *
   * @api private
   */

  var indicator = global.document && "MozAppearance" in
    global.document.documentElement.style;

  /**
   * Expose constructor.
   */

  exports['jsonp-polling'] = JSONPPolling;

  /**
   * The JSONP transport creates an persistent connection by dynamically
   * inserting a script tag in the page. This script tag will receive the
   * information of the Socket.IO server. When new information is received
   * it creates a new script tag for the new data stream.
   *
   * @constructor
   * @extends {io.Transport.xhr-polling}
   * @api public
   */

  function JSONPPolling (socket) {
    io.Transport['xhr-polling'].apply(this, arguments);

    this.index = io.j.length;

    var self = this;

    io.j.push(function (msg) {
      self._(msg);
    });
  };

  /**
   * Inherits from XHR polling transport.
   */

  io.util.inherit(JSONPPolling, io.Transport['xhr-polling']);

  /**
   * Transport name
   *
   * @api public
   */

  JSONPPolling.prototype.name = 'jsonp-polling';

  /**
   * Posts a encoded message to the Socket.IO server using an iframe.
   * The iframe is used because script tags can create POST based requests.
   * The iframe is positioned outside of the view so the user does not
   * notice it's existence.
   *
   * @param {String} data A encoded message.
   * @api private
   */

  JSONPPolling.prototype.post = function (data) {
    var self = this
      , query = io.util.query(
             this.socket.options.query
          , 't='+ (+new Date) + '&i=' + this.index
        );

    if (!this.form) {
      var form = document.createElement('form')
        , area = document.createElement('textarea')
        , id = this.iframeId = 'socketio_iframe_' + this.index
        , iframe;

      form.className = 'socketio';
      form.style.position = 'absolute';
      form.style.top = '0px';
      form.style.left = '0px';
      form.style.display = 'none';
      form.target = id;
      form.method = 'POST';
      form.setAttribute('accept-charset', 'utf-8');
      area.name = 'd';
      form.appendChild(area);
      document.body.appendChild(form);

      this.form = form;
      this.area = area;
    }

    this.form.action = this.prepareUrl() + query;

    function complete () {
      initIframe();
      self.socket.setBuffer(false);
    };

    function initIframe () {
      if (self.iframe) {
        self.form.removeChild(self.iframe);
      }

      try {
        // ie6 dynamic iframes with target="" support (thanks Chris Lambacher)
        iframe = document.createElement('<iframe name="'+ self.iframeId +'">');
      } catch (e) {
        iframe = document.createElement('iframe');
        iframe.name = self.iframeId;
      }

      iframe.id = self.iframeId;

      self.form.appendChild(iframe);
      self.iframe = iframe;
    };

    initIframe();

    // we temporarily stringify until we figure out how to prevent
    // browsers from turning `\n` into `\r\n` in form inputs
    this.area.value = io.JSON.stringify(data);

    try {
      this.form.submit();
    } catch(e) {}

    if (this.iframe.attachEvent) {
      iframe.onreadystatechange = function () {
        if (self.iframe.readyState == 'complete') {
          complete();
        }
      };
    } else {
      this.iframe.onload = complete;
    }

    this.socket.setBuffer(true);
  };

  /**
   * Creates a new JSONP poll that can be used to listen
   * for messages from the Socket.IO server.
   *
   * @api private
   */

  JSONPPolling.prototype.get = function () {
    var self = this
      , script = document.createElement('script')
      , query = io.util.query(
             this.socket.options.query
          , 't='+ (+new Date) + '&i=' + this.index
        );

    if (this.script) {
      this.script.parentNode.removeChild(this.script);
      this.script = null;
    }

    script.async = true;
    script.src = this.prepareUrl() + query;
    script.onerror = function () {
      self.onClose();
    };

    var insertAt = document.getElementsByTagName('script')[0];
    insertAt.parentNode.insertBefore(script, insertAt);
    this.script = script;

    if (indicator) {
      setTimeout(function () {
        var iframe = document.createElement('iframe');
        document.body.appendChild(iframe);
        document.body.removeChild(iframe);
      }, 100);
    }
  };

  /**
   * Callback function for the incoming message stream from the Socket.IO server.
   *
   * @param {String} data The message
   * @api private
   */

  JSONPPolling.prototype._ = function (msg) {
    this.onData(msg);
    if (this.isOpen) {
      this.get();
    }
    return this;
  };

  /**
   * The indicator hack only works after onload
   *
   * @param {Socket} socket The socket instance that needs a transport
   * @param {Function} fn The callback
   * @api private
   */

  JSONPPolling.prototype.ready = function (socket, fn) {
    var self = this;
    if (!indicator) return fn.call(this);

    io.util.load(function () {
      fn.call(self);
    });
  };

  /**
   * Checks if browser supports this transport.
   *
   * @return {Boolean}
   * @api public
   */

  JSONPPolling.check = function () {
    return 'document' in global;
  };

  /**
   * Check if cross domain requests are supported
   *
   * @returns {Boolean}
   * @api public
   */

  JSONPPolling.xdomainCheck = function () {
    return true;
  };

  /**
   * Add the transport to your public io.transports array.
   *
   * @api private
   */

  io.transports.push('jsonp-polling');

})(
    'undefined' != typeof io ? io.Transport : module.exports
  , 'undefined' != typeof io ? io : module.parent.exports
  , this
);

if (typeof define === "function" && define.amd) {
  define("socket.io", [], function () { return io; });
}
})();
/* @source mod/liveupdate.js */;

define('socket.io', 'lib/socket.io.js');
define('mod/liveupdate', [
  "jquery",
  "jquery-tmpl",
  "socket.io"
], function ($, _) {
    //var server = 'http://doubandev2.intra.douban.com:7076';
    var server = 'http://code.intra.douban.com:7076';
    var live = io.connect(server, {
      'reconnect': true,
      'reconnection delay': 500,
      'max reconnection attempts': 10
    });

    var roomPeoples = {};
    live.on('announce', function(data){
      var user = data.username;
      if(user !== undefined && user in roomPeoples === false) {
        roomPeoples[user] = user;
        var user_html = '<a class="avatar tooltipped downwards"><img height="24" width="24" alt="'+user+'" src="'+data.avatar+'"></a>';
        $('#room_peoples .quickstat').show();
        $('#room_peoples').append(user_html);
      }

      if(data.type === 'typing') {
        $('#typing').show();
        $('#typing span').html(data.username+' is typing......');
      }
      else if(data.type === 'merge') {
        $(".pull-state span").html("Merged");
        $(".merge-guide").hide();
        var merged_time = new Date();
        $("#changelog").append($.tmpl($("#render_node_merge"),
                                      {'merged_time': merged_time,
                                       'user':data.username,
                                       'avatar': data.avatar}));
      }
      else {
        $('#typing').hide();
        $('#changelog').append(data.message);
      }
    });

    return live;
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

/* @source mod/diff.js */;

define('mod/diff', [
  "jquery",
  "mod/input-ext",
  "mod/liveupdate",
  "mod/colorcube"
], function ($, inputExt, live, colorcube) {

        ////////////////////  linecomment

        // comment form
        var hideCommentForm = function () {
            $('.inline-comment-form').hide().closest('tr').removeClass('show-inline-comment-form');
            $('.inline-comment-form').each(
                function (idx, el) {
                    if (!$(el).siblings('.comment-holder').children('.comment').length) {
                        $(el).parents('tr').hide();
                    }
                }
            );
        };
        var openCommentForm = function (curRow) {
            hideCommentForm();
            var nextRow = curRow.next('tr');
            // if no comments on curRow yet
            if (!nextRow.length || !nextRow.hasClass('inline-comments')) {
                nextRow = $.tmpl($('#templ-inline-comments-row'), {}).insertAfter(curRow);
            }
            // if side by side... plz refactor this
            var file = curRow.parents('.file');
            if ((file.children('.side')).length != 0 && file.children('.side').css('display') != 'none') {
                $(nextRow.children()[0]).attr('colspan', 1);
            }
            nextRow.show().addClass('show-inline-comment-form');
            var commentsBlock = nextRow.children('.line-comments'),
            commentForm = commentsBlock.find('.inline-comment-form');
            // if no commentForm on nextRow yet
            if (!commentForm.length) {
                // get form-data
                var patch_data = file.children('.meta').find('.patch-data');
                var line_data = curRow.find('.line-data');
                var data = {
                    from_sha: patch_data.attr('data-from-sha'),
                    old_path: patch_data.attr('data-old-path'),
                    new_path: patch_data.attr('data-new-path'),
                    from_oid: patch_data.attr('data-from-oid'),
                    to_oid:   patch_data.attr('data-to-oid'),
                    old_no: line_data.attr('data-old'),
                    new_no: line_data.attr('data-new'),
                };
                commentForm = $.tmpl($('#templ-inline-comment-form'), data).appendTo(commentsBlock);
                commentForm.find('.js-hide-inline-comment-form').click(
                    function () {
                        hideCommentForm();
                    }
                ).end().find('form').submit(
                    function () {
                        $(this).find('button[type="submit"]').attr('disabled', true).addClass('disabled');
                        return true;
                    }
                );
                var commentTexarea = commentForm.find('textarea');
                inputExt.enableEmojiInput(commentTexarea);
                inputExt.shortcut2submit(commentTexarea);
            }
            commentForm.show().find('textarea').focus();
            // codelive channel
            var linecomment_channel_id;
            if ($('.discussion-tab-link').length > 0) {
                linecomment_channel_id = "code_pr_"+$('.discussion-tab-link').attr('data-url') + 'linecomment';
            }
            // `comment on this line`
            commentForm.find('form.js-inline-comment-form').ajaxForm({
                dataType: 'json',
                beforeSend: function () {
                    commentForm.find('button[type="submit"]').attr('disabled', true).addClass('disabled')
                    .end().find('.loader').show();
                },
                success: function(r) {
                    if (r.r == 0 && r.html) {
                        commentForm.siblings('.js-comments-holder').append(r.html);
                        commentForm.find('textarea').val('').blur();
                        hideCommentForm();
                        live && linecomment_channel_id &&
                            live.emit('ready', {channel: linecomment_channel_id, msg:r.html_with_diff});
                    } else if (r.error){
                        alert(r.error);
                    }
                    commentForm.find('button[type="submit"]').attr('disabled', false).removeClass('disabled');
                    commentForm.find('form.js-inline-comment-form').removeClass('submitting')
                    .end().find('.loader').hide();
                    return true;
                },
                error: function () {}
            });
        };

        // add-bubble...
        $('body').delegate('.add-bubble', 'click', function () {
            var curRow = $(this).parents('tr');
            var nextRow = curRow.next('tr');
            if (nextRow.hasClass('inline-comments') && nextRow.css('display') != 'none') {
                nextRow.hide();
            } else {
                openCommentForm(curRow);
            }
        });

        // `add a line note`
        $('body').delegate(
            '.js-show-inline-comment-form', 'click', function () {
            var curRow = $(this).parents('tr').prev('tr');
            openCommentForm(curRow);
        });

        // linecomment delete
        $('body').delegate('.inline-comments .delete-button', 'click', function (e) {
            if (!confirm('Are you sure you want to delete this?')) {
                return false;
            }
            var comment = $(this).parents('.comment');
            $.getJSON(
                $(this).attr('href'),
                function(r) {
                    // FIXME: global row?
                    if (r.r == '1')
                        var row = comment.parents('tr');
                    if (comment.siblings('.comment').length ||
                        row.find('.inline-comment-form').length) {
                        comment.remove();
                    } else {
                        row.remove();
                    }
                }
            );
            return false;
        });

        // comment & linecomment edit
        $('body').delegate('.js-comment-edit-button', 'click', function (e) {
            var form_content = $(this).parents('.comment-header')
            .next('.comment-content')
            .children('.form-content');
            if (form_content != undefined) {
                form_content.show().find('textarea').focus();
                form_content.find('form.js-comment-update').ajaxForm({
                    dataType: 'json',
                    beforeSend: function() {
                        form_content.find('button[type="submit"]').attr('disabled', true).addClass('disabled')
                        .end().find('.loader').show();
                    },
                    success: function(r) {
                        if (r.r == 0 && r.html) {
                            if (form_content.find('textarea').attr('name') === 'pull_request_review_comment'){
                                form_content.parents('.js-comments-holder').append(r.html);
                                form_content.parents('.comment').remove();
                            } else {
                                var comment = form_content.parents('.change');
                                var avatar = comment.prev('.side-avatar');
                                form_content.parents('#changelog').append(r.html);
                                comment.remove();
                                avatar.remove();
                            }
                        }
                        return true;
                    }
                });
            } else {
                return false;
            }
        });

        // show linecomments toggle
        $('body').delegate('.file .js-show-inline-comments-toggle', 'change', function () {
            var comments = $(this).parents('.file').find('.inline-comments');
            if ($(this).is(':checked')) {
                comments.show();
            } else {
                comments.hide();
            }
        });

        // generated file toggle
        $('body').delegate('.file a.generated', 'click', function() {
            var file = $(this).parents('.file');
            var inline = file.children('.inline').show();
            $(this).hide();
        });

        // patch side diff toggle
        $('body').delegate('.file .js-side-diff', 'click', function () {
            var file = $(this).parents('.file');
            file.find('a.generated').hide();
            if (file.children('.side').css('display') === 'none' &&
                file.children('.inline').css('display') === 'none'){
                file.children('.inline').show();
            }else {
                var inline = file.children('.inline').toggle();
                var side = file.children('.side').toggle();
                var checkbox = file.find('.js-show-inline-comments-toggle');
                if (file.children('.side').css('display') != 'none') {
                    checkbox.attr('checked', false);
                    side.find('.inline-comments').hide();
                }
                else {
                    checkbox.attr('checked', true);
                }
            }
        });

        // diff patch fullscreen toggle
        $('body').delegate('.file .js-fullscreen', 'click', function () {
            var fullscreenStage = $('#fullscreen-stage');
            if (fullscreenStage.length == 0) {
                var files = $(this).parents('#files');
                fullscreenStage = $('<div id="fullscreen-stage"></div>').appendTo(files);
            }
            if (fullscreenStage.is(":visible")) {
                fullscreenStage.hide();
                $('body').removeClass('fullscreen-mode');
            } else {
                var file = $(this).parents('.file');
                fullscreenStage.html(file.clone()).show();
                $('body').addClass('fullscreen-mode');
                fullscreenStage.find('.file .js-fullscreen').text('Exit Full Screen');
            }
        });

        // dblclick open linecomment form
        var clearSelection = function () {
            if (window.getSelection) {
              if (window.getSelection().empty) {  // Chrome
                window.getSelection().empty();
              } else if (window.getSelection().removeAllRanges) {  // Firefox
                window.getSelection().removeAllRanges();
              }
            } else if (document.selection) {  // IE?
              document.selection.empty();
            }
        }
        $('body').delegate('.js-open-comment-form.dblclick-comment', 'dblclick', function () {
            clearSelection();
            var curRow = $(this).parents('tr');
            openCommentForm(curRow);
        });

        ////////////////////  moreline get_contexts

        // moreline
        $('body').delegate('pre.skipped a', 'click', function() {
            var curRow = $(this).parents('tr');
            var patch_data = curRow.parents('.file').children('.meta').find('.patch-data');
            var data = curRow.find('.expand-data');
            var url = patch_data.attr('data-context-url');
            $.get(
                url,
                {
                    old_sha   : patch_data.attr('data-old-sha'),
                    old_path  : patch_data.attr('data-old-path'),
                    old_start : data.attr('data-old-start'),
                    new_start : data.attr('data-new-start'),
                    old_end   : data.attr('data-old-end'),
                    new_end   : data.attr('data-new-end'),
                    type      : $(this).attr('data-type'),
                },
                function (r) {
                    curRow.after(r.html);
                    if (r.html.trim()) {
                        curRow.remove();
                    }
                }
            );
        });

        // full diff
        $('body').delegate('.ellipsis', 'click', function() {
            var $this = $(this);
            var fpath = $this.attr('data-path');
            var new_fpath = $this.attr('data-new-path');

            // for pull/new
            var from_proj = $('.new-pull-request form input[name="from_proj"]').attr('value');
            var from_ref = $('.new-pull-request form input[name="from_ref"]').attr('value');
            var to_ref = $('.new-pull-request form input[name="to_ref"]').attr('value');
            var to_proj = $('.new-pull-request form input[name="to_proj"]').attr('value');

            var url = $this.attr('data-url');
            var table = $this.parents('.data').find('.diff-table');
            $.get(url,
                  {
                      filepath: fpath,
                      new_filepath: new_fpath,
                      from_proj: from_proj,
                      from_ref: from_ref,
                      to_ref: to_ref,
                      to_proj: to_proj
                  },
                  function(r){
                      table.find('tbody').html(r.html);
                  });
        });

        // TODO: modify this, after refactor diff api
        // toggle whitespace diff
        $('body').delegate('.toggle_whitespace', 'click', function() {
            var $this = $(this);
            var fpath = $this.attr('data-path');
            var new_fpath = $this.attr('data-new-path');

             // for pull/new
            var from_proj = $('.new-pull-request form input[name="from_proj"]').attr('value');
            var from_ref = $('.new-pull-request form input[name="from_ref"]').attr('value');
            var to_ref = $('.new-pull-request form input[name="to_ref"]').attr('value');
            var to_proj = $('.new-pull-request form input[name="to_proj"]').attr('value');

            var url = $this.attr('data-url');
            var table = $this.parents('.data').find('.diff-table');
            var whitespace = $this.attr('data-w');

            $.get(url,
                  {
                      filepath: fpath,
                      new_filepath: new_fpath,
                      from_proj: from_proj,
                      from_ref: from_ref,
                      to_ref: to_ref,
                      to_proj: to_proj,
                      w: whitespace
                  },
                  function(r){
                      table.find('tbody').html(r.html);
                      $this.attr('data-w', (1 - parseInt(whitespace)).toString());
                  });
        });

        //////////////////// no use ??
        function convertDiff(name, table, pre) {
          var inline = $(table).hasClass('inline');
          var ths = table.tHead.rows[0].cells;
          var afile, bfile;
          if ( inline ) {
              afile = ths[0].title;
              bfile = ths[1].title;
          } else {
              afile = $(ths[0]).find('a').text();
              bfile = $(ths[1]).find('a').text();
          }
          if ( afile.match(/^Revision /) ) {
              afile = 'a/' + name;
              bfile = 'b/' + name;
          }
          var lines = [
            "Index: " + name,
            "===================================================================",
            "--- " + afile.replace(/File /, ''),
            "+++ " + bfile.replace(/File /, ''),
          ];
          var sepIndex = 0;
          var oldOffset = 0, oldLength = 0, newOffset = 0, newLength = 0;
          var title = "";
          if (inline)
            title = $(ths[2]).text();
          for (var i = 0; i < table.tBodies.length; i++) {
            var tBody = table.tBodies[i];
            if (i == 0 || tBody.className == "skipped") {
              if (i > 0) {
                if (!oldOffset && oldLength) oldOffset = 1
                if (!newOffset && newLength) newOffset = 1
                lines[sepIndex] = lines[sepIndex]
                  .replace("{1}", oldOffset).replace("{2}", oldLength)
                  .replace("{3}", newOffset).replace("{4}", newLength)
                  .replace("{5}", title);
              }
              sepIndex = lines.length;
              lines.push("@@ -{1},{2} +{3},{4} @@{5}");
              oldOffset = 0, oldLength = 0, newOffset = 0, newLength = 0;
              if (tBody.className == "skipped") {
                if (inline)
                  title = $(tBody.rows[0].cells[2]).text();
                continue;
              }
            }
            var tmpLines = [];
            for (var j = 0; j < tBody.rows.length; j++) {
              var cells = tBody.rows[j].cells;
              var oldLineNo = parseInt($(cells[0]).text());
              var newLineNo = parseInt($(cells[inline ? 1 : 2]).text());
              if (tBody.className == 'unmod') {
                lines.push(" " + $(cells[inline ? 2 : 1]).text());
                oldLength += 1;
                newLength += 1;
                if (!oldOffset) oldOffset = oldLineNo;
                if (!newOffset) newOffset = newLineNo;
              } else {
                var oldLine;
                var newLine;
                var oldTag = "-";
                var newTag = "+";
                if (inline) {
                  oldLine = newLine = $(cells[2]).text();
                  if ($('em', cells[2]).length) oldTag = newTag = "\\";
                } else {
                  oldLine = $(cells[1]).text();
                  if ($('em', cells[1]).length) oldTag = "\\";
                  newLine = $(cells[3]).text();
                  if ($('em', cells[3]).length) newTag = "\\";
                }
                if (!isNaN(oldLineNo)) {
                  lines.push(oldTag + oldLine);
                  oldLength += 1;
                }
                if (!isNaN(newLineNo)) {
                  tmpLines.push(newTag + newLine);
                  newLength += 1;
                }
              }
            }
            if (tmpLines.length > 0) {
              lines = lines.concat(tmpLines);
            }
          }
          if (!oldOffset && oldLength) oldOffset = 1;
          if (!newOffset && newLength) newOffset = 1;
          lines[sepIndex] = lines[sepIndex]
            .replace("{1}", oldOffset).replace("{2}", oldLength)
            .replace("{3}", newOffset).replace("{4}", newLength)
            .replace("{5}", title);
          /* remove trailing &nbsp; and join lines (with CR for IExplorer) */
          var sep = $.browser.msie ? "\r" : "\n";
          for ( var i = 0; i < lines.length; i++ )
              if ( lines[i] )
              {
                  var line = lines[i].replace(/\xa0$/, '') + sep;
                  if ( lines[i][0] == '+' )
                    pre.append($('<span class="add">').text(line));
                  else if ( lines[i][0] == '-' )
                    pre.append($('<span class="rem">').text(line));
                  else
                    pre.append($('<span>').text(line));
              }
        }
        // no use ??
        $("div.diff h2").each(function() {
          console.log('call div.diff h2 !!!');
          var switcher = $("<span class='switch'></span>").prependTo(this);
          var name = $.trim($(this).text());
          var table = $(this).siblings("table").get(0);
          if (! table) return;
          var pre = $('<pre class="diff">').hide().insertAfter(table);
          $("<span>" + _("Tabular") + "</span>").click(function() {
            $(pre).hide();
            $(table).show();
            $(this).addClass("active").siblings("span").removeClass("active");
            return false;
          }).addClass("active").appendTo(switcher);
          $("<span>" + _("Unified") + "</span>").click(function() {
            $(table).hide();
            if (!pre.get(0).firstChild) convertDiff(name, table, pre);
            $(pre).fadeIn("fast")
            $(this).addClass("active").siblings("span").removeClass("active");
            return false;
          }).appendTo(switcher);
        });


        colorcube.init({target:'body'});
});

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

/* @source lib/jquery.caret.js */;


/*
   Implement Twitter/Weibo @ mentions

   Copyright (c) 2012 chord.luo@gmail.com

   Permission is hereby granted, free of charge, to any person obtaining
   a copy of this software and associated documentation files (the
   "Software"), to deal in the Software without restriction, including
   without limitation the rights to use, copy, modify, merge, publish,
   distribute, sublicense, and/or sell copies of the Software, and to
   permit persons to whom the Software is furnished to do so, subject to
   the following conditions:

   The above copyright notice and this permission notice shall be
   included in all copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
   LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
   OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
   WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

/*
本插件操作 textarea 或者 input 内的插入符
只实现了获得插入符在文本框中的位置，以及设置
插入符的位置.
*/

(function() {

  (function($) {
    var getCaretPos, setCaretPos;
    getCaretPos = function(inputor) {
      var end, endRange, len, normalizedValue, pos, range, start, textInputRange;
      if (document.selection) {
        /*
                    #assume we select "HATE" in the inputor such as textarea -> { }.
                     *               start end-point.
                     *              /
                     * <  I really [HATE] IE   > between the brackets is the selection range.
                     *                   \
                     *                    end end-point.
        */
        range = document.selection.createRange();
        pos = 0;
        if (range && range.parentElement() === inputor) {
          normalizedValue = inputor.value.replace(/\r\n/g, "\n");
          /* SOMETIME !!! 
           "/r/n" is counted as two char.
            one line is two, two will be four. balalala.
            so we have to using the normalized one's length.;
          */
          len = normalizedValue.length;
          /*
                             <[  I really HATE IE   ]>:
                              the whole content in the inputor will be the textInputRange.
          */
          textInputRange = inputor.createTextRange();
          /*                 _here must be the position of bookmark.
                           /
             <[  I really [HATE] IE   ]>
              [---------->[           ] : this is what moveToBookmark do.
             <   I really [[HATE] IE   ]> : here is result.
                            \ two brackets in should be in line.
          */
          textInputRange.moveToBookmark(range.getBookmark());
          endRange = inputor.createTextRange();
          /*  [--------------------->[] : if set false all end-point goto end.
            <  I really [[HATE] IE  []]>
          */
          endRange.collapse(false);
          /*
                                          ___VS____
                                         /         \
                           <   I really [[HATE] IE []]>
                                                    \_endRange end-point.
                          
                          " > -1" mean the start end-point will be the same or right to the end end-point
                         * simplelly, all in the end.
          */
          if (textInputRange.compareEndPoints("StartToEnd", endRange) > -1) {
            start = end = len;
          } else {
            /*
                                        I really |HATE] IE   ]> 
                                               <-|
                                      I really[ [HATE] IE   ]>
                                            <-[
                                    I reall[y  [HATE] IE   ]>
                                 
                                  will return how many unit have moved.
            */
            start = -textInputRange.moveStart("character", -len);
            end = -textInputRange.moveEnd("character", -len);
          }
        }
      } else {
        start = inputor.selectionStart;
      }
      return start;
    };
    setCaretPos = function(inputor, pos) {
      var range;
      if (document.selection) {
        range = inputor.createTextRange();
        range.move("character", pos);
        return range.select();
      } else {
        return inputor.setSelectionRange(pos, pos);
      }
    };
    return $.fn.caretPos = function(pos) {
      var inputor;
      inputor = this[0];
      inputor.focus();
      if (pos) {
        return setCaretPos(inputor, pos);
      } else {
        return getCaretPos(inputor);
      }
    };
  })(window.jQuery);

}).call(this);

/* autogeneration */
define("lib/jquery.caret", [], function(){});

/* @source mod/quick_emoji.js */;

define("mod/quick_emoji", [
  "jquery",
  "lib/jquery.caret",
  "bootstrap"
],
        function($) {
            var quick_emoji = {};
            quick_emoji.enable = function(textarea_query){
                $('body').delegate('.quick-emoji a', 'click', function(e){
                    var emoji = $(this).attr('data-emoji');
                    if(emoji){
                        textarea = $(textarea_query);
                        var caretpos = textarea.caretPos();
                        var content = textarea.val();
                        var result = "";
                        if(content) {
                            result = content.slice(0, caretpos) + ' ' +
                                emoji + ' ' + content.slice(caretpos);
                            textarea.val(result);
                            textarea.caretPos(caretpos + emoji.length + 2);
                        }
                        else {
                            result = emoji;
                            textarea.val(result);
                            textarea.caretPos(result.length);
                        }
                    }
                    return false;
                });

                $('body').delegate('.emojis a', 'hover', function(e){
                    var $zoomDiv = $('.zoom');
                    if (e.type == "mouseenter") {
                        var $emojiUrl = $(this).find('img').attr('src');
                        var $zoomImage = $('.zoom-image');
                        var $tabContent = $('.tab-content');
                        $zoomImage.attr('src', $emojiUrl);
                        $zoomDiv.css({'display': 'block'});
                    } else {
                        $zoomDiv.css({'display': 'none'});
                    }
                });
            }
                return quick_emoji;
            });

/* @source lib/pixastic.custom.js */;

/*
 * Pixastic - JavaScript Image Processing Library
 * Copyright (c) 2008 Jacob Seidelin, jseidelin@nihilogic.dk, http://blog.nihilogic.dk/
 * MIT License [http://www.pixastic.com/lib/license.txt]
 */


var Pixastic=(function(){function addEvent(el,event,handler){if(el.addEventListener)
el.addEventListener(event,handler,false);else if(el.attachEvent)
el.attachEvent("on"+event,handler);}
function onready(handler){var handlerDone=false;var execHandler=function(){if(!handlerDone){handlerDone=true;handler();}}
document.write("<"+"script defer src=\"//:\" id=\"__onload_ie_pixastic__\"></"+"script>");var script=document.getElementById("__onload_ie_pixastic__");script.onreadystatechange=function(){if(script.readyState=="complete"){script.parentNode.removeChild(script);execHandler();}}
if(document.addEventListener)
document.addEventListener("DOMContentLoaded",execHandler,false);addEvent(window,"load",execHandler);}
function init(){var imgEls=getElementsByClass("pixastic",null,"img");var canvasEls=getElementsByClass("pixastic",null,"canvas");var elements=imgEls.concat(canvasEls);for(var i=0;i<elements.length;i++){(function(){var el=elements[i];var actions=[];var classes=el.className.split(" ");for(var c=0;c<classes.length;c++){var cls=classes[c];if(cls.substring(0,9)=="pixastic-"){var actionName=cls.substring(9);if(actionName!="")
actions.push(actionName);}}
if(actions.length){if(el.tagName.toLowerCase()=="img"){var dataImg=new Image();dataImg.src=el.src;if(dataImg.complete){for(var a=0;a<actions.length;a++){var res=Pixastic.applyAction(el,el,actions[a],null);if(res)
el=res;}}else{dataImg.onload=function(){for(var a=0;a<actions.length;a++){var res=Pixastic.applyAction(el,el,actions[a],null)
if(res)
el=res;}}}}else{setTimeout(function(){for(var a=0;a<actions.length;a++){var res=Pixastic.applyAction(el,el,actions[a],null);if(res)
el=res;}},1);}}})();}}
if(typeof pixastic_parseonload!="undefined"&&pixastic_parseonload)
onready(init);function getElementsByClass(searchClass,node,tag){var classElements=new Array();if(node==null)
node=document;if(tag==null)
tag='*';var els=node.getElementsByTagName(tag);var elsLen=els.length;var pattern=new RegExp("(^|\\s)"+searchClass+"(\\s|$)");for(i=0,j=0;i<elsLen;i++){if(pattern.test(els[i].className)){classElements[j]=els[i];j++;}}
return classElements;}
var debugElement;function writeDebug(text,level){if(!Pixastic.debug)return;try{switch(level){case"warn":console.warn("Pixastic:",text);break;case"error":console.error("Pixastic:",text);break;default:console.log("Pixastic:",text);}}catch(e){}
if(!debugElement){}}
var hasCanvas=(function(){var c=document.createElement("canvas");var val=false;try{val=!!((typeof c.getContext=="function")&&c.getContext("2d"));}catch(e){}
return function(){return val;}})();var hasCanvasImageData=(function(){var c=document.createElement("canvas");var val=false;var ctx;try{if(typeof c.getContext=="function"&&(ctx=c.getContext("2d"))){val=(typeof ctx.getImageData=="function");}}catch(e){}
return function(){return val;}})();var hasGlobalAlpha=(function(){var hasAlpha=false;var red=document.createElement("canvas");if(hasCanvas()&&hasCanvasImageData()){red.width=red.height=1;var redctx=red.getContext("2d");redctx.fillStyle="rgb(255,0,0)";redctx.fillRect(0,0,1,1);var blue=document.createElement("canvas");blue.width=blue.height=1;var bluectx=blue.getContext("2d");bluectx.fillStyle="rgb(0,0,255)";bluectx.fillRect(0,0,1,1);redctx.globalAlpha=0.5;redctx.drawImage(blue,0,0);var reddata=redctx.getImageData(0,0,1,1).data;hasAlpha=(reddata[2]!=255);}
return function(){return hasAlpha;}})();return{parseOnLoad:false,debug:false,applyAction:function(img,dataImg,actionName,options){options=options||{};var imageIsCanvas=(img.tagName.toLowerCase()=="canvas");if(imageIsCanvas&&Pixastic.Client.isIE()){if(Pixastic.debug)writeDebug("Tried to process a canvas element but browser is IE.");return false;}
var canvas,ctx;var hasOutputCanvas=false;if(Pixastic.Client.hasCanvas()){hasOutputCanvas=!!options.resultCanvas;canvas=options.resultCanvas||document.createElement("canvas");ctx=canvas.getContext("2d");}
var w=img.offsetWidth;var h=img.offsetHeight;if(imageIsCanvas){w=img.width;h=img.height;}
if(w==0||h==0){if(img.parentNode==null){var oldpos=img.style.position;var oldleft=img.style.left;img.style.position="absolute";img.style.left="-9999px";document.body.appendChild(img);w=img.offsetWidth;h=img.offsetHeight;document.body.removeChild(img);img.style.position=oldpos;img.style.left=oldleft;}else{if(Pixastic.debug)writeDebug("Image has 0 width and/or height.");return;}}
if(actionName.indexOf("(")>-1){var tmp=actionName;actionName=tmp.substr(0,tmp.indexOf("("));var arg=tmp.match(/\((.*?)\)/);if(arg[1]){arg=arg[1].split(";");for(var a=0;a<arg.length;a++){thisArg=arg[a].split("=");if(thisArg.length==2){if(thisArg[0]=="rect"){var rectVal=thisArg[1].split(",");options[thisArg[0]]={left:parseInt(rectVal[0],10)||0,top:parseInt(rectVal[1],10)||0,width:parseInt(rectVal[2],10)||0,height:parseInt(rectVal[3],10)||0}}else{options[thisArg[0]]=thisArg[1];}}}}}
if(!options.rect){options.rect={left:0,top:0,width:w,height:h};}else{options.rect.left=Math.round(options.rect.left);options.rect.top=Math.round(options.rect.top);options.rect.width=Math.round(options.rect.width);options.rect.height=Math.round(options.rect.height);}
var validAction=false;if(Pixastic.Actions[actionName]&&typeof Pixastic.Actions[actionName].process=="function"){validAction=true;}
if(!validAction){if(Pixastic.debug)writeDebug("Invalid action \""+actionName+"\". Maybe file not included?");return false;}
if(!Pixastic.Actions[actionName].checkSupport()){if(Pixastic.debug)writeDebug("Action \""+actionName+"\" not supported by this browser.");return false;}
if(Pixastic.Client.hasCanvas()){if(canvas!==img){canvas.width=w;canvas.height=h;}
if(!hasOutputCanvas){canvas.style.width=w+"px";canvas.style.height=h+"px";}
ctx.drawImage(dataImg,0,0,w,h);if(!img.__pixastic_org_image){canvas.__pixastic_org_image=img;canvas.__pixastic_org_width=w;canvas.__pixastic_org_height=h;}else{canvas.__pixastic_org_image=img.__pixastic_org_image;canvas.__pixastic_org_width=img.__pixastic_org_width;canvas.__pixastic_org_height=img.__pixastic_org_height;}}else if(Pixastic.Client.isIE()&&typeof img.__pixastic_org_style=="undefined"){img.__pixastic_org_style=img.style.cssText;}
var params={image:img,canvas:canvas,width:w,height:h,useData:true,options:options}
var res=Pixastic.Actions[actionName].process(params);if(!res){return false;}
if(Pixastic.Client.hasCanvas()){if(params.useData){if(Pixastic.Client.hasCanvasImageData()){canvas.getContext("2d").putImageData(params.canvasData,options.rect.left,options.rect.top);canvas.getContext("2d").fillRect(0,0,0,0);}}
if(!options.leaveDOM){canvas.title=img.title;canvas.imgsrc=img.imgsrc;if(!imageIsCanvas)canvas.alt=img.alt;if(!imageIsCanvas)canvas.imgsrc=img.src;canvas.className=img.className;canvas.style.cssText=img.style.cssText;canvas.name=img.name;canvas.tabIndex=img.tabIndex;canvas.id=img.id;if(img.parentNode&&img.parentNode.replaceChild){img.parentNode.replaceChild(canvas,img);}}
options.resultCanvas=canvas;return canvas;}
return img;},prepareData:function(params,getCopy){var ctx=params.canvas.getContext("2d");var rect=params.options.rect;var dataDesc=ctx.getImageData(rect.left,rect.top,rect.width,rect.height);var data=dataDesc.data;if(!getCopy)params.canvasData=dataDesc;return data;},process:function(img,actionName,options,callback){if(img.tagName.toLowerCase()=="img"){var dataImg=new Image();dataImg.src=img.src;if(dataImg.complete){var res=Pixastic.applyAction(img,dataImg,actionName,options);if(callback)callback(res);return res;}else{dataImg.onload=function(){var res=Pixastic.applyAction(img,dataImg,actionName,options)
if(callback)callback(res);}}}
if(img.tagName.toLowerCase()=="canvas"){var res=Pixastic.applyAction(img,img,actionName,options);if(callback)callback(res);return res;}},revert:function(img){if(Pixastic.Client.hasCanvas()){if(img.tagName.toLowerCase()=="canvas"&&img.__pixastic_org_image){img.width=img.__pixastic_org_width;img.height=img.__pixastic_org_height;img.getContext("2d").drawImage(img.__pixastic_org_image,0,0);if(img.parentNode&&img.parentNode.replaceChild){img.parentNode.replaceChild(img.__pixastic_org_image,img);}
return img;}}else if(Pixastic.Client.isIE()){if(typeof img.__pixastic_org_style!="undefined")
img.style.cssText=img.__pixastic_org_style;}},Client:{hasCanvas:hasCanvas,hasCanvasImageData:hasCanvasImageData,hasGlobalAlpha:hasGlobalAlpha,isIE:function(){return!!document.all&&!!window.attachEvent&&!window.opera;}},Actions:{}}})();Pixastic.Actions.blend={process:function(params){var amount=parseFloat(params.options.amount);var mode=(params.options.mode||"normal").toLowerCase();var image=params.options.image;amount=Math.max(0,Math.min(1,amount));if(!image)return false;if(Pixastic.Client.hasCanvasImageData()){var rect=params.options.rect;var data=Pixastic.prepareData(params);var w=rect.width;var h=rect.height;params.useData=false;var otherCanvas=document.createElement("canvas");otherCanvas.width=params.canvas.width;otherCanvas.height=params.canvas.height;var otherCtx=otherCanvas.getContext("2d");otherCtx.drawImage(image,0,0);var params2={canvas:otherCanvas,options:params.options};var data2=Pixastic.prepareData(params2);var dataDesc2=params2.canvasData;var p=w*h;var pix=p*4;var pix1,pix2;var r1,g1,b1;var r2,g2,b2;var r3,g3,b3;var r4,g4,b4;var dataChanged=false;switch(mode){case"normal":break;case"multiply":while(p--){data2[pix-=4]=data[pix]*data2[pix]/255;data2[pix1=pix+1]=data[pix1]*data2[pix1]/255;data2[pix2=pix+2]=data[pix2]*data2[pix2]/255;}
dataChanged=true;break;case"lighten":while(p--){if((r1=data[pix-=4])>data2[pix])
data2[pix]=r1;if((g1=data[pix1=pix+1])>data2[pix1])
data2[pix1]=g1;if((b1=data[pix2=pix+2])>data2[pix2])
data2[pix2]=b1;}
dataChanged=true;break;case"darken":while(p--){if((r1=data[pix-=4])<data2[pix])
data2[pix]=r1;if((g1=data[pix1=pix+1])<data2[pix1])
data2[pix1]=g1;if((b1=data[pix2=pix+2])<data2[pix2])
data2[pix2]=b1;}
dataChanged=true;break;case"darkercolor":while(p--){if(((r1=data[pix-=4])*0.3+(g1=data[pix1=pix+1])*0.59+(b1=data[pix2=pix+2])*0.11)<=(data2[pix]*0.3+data2[pix1]*0.59+data2[pix2]*0.11)){data2[pix]=r1;data2[pix1]=g1;data2[pix2]=b1;}}
dataChanged=true;break;case"lightercolor":while(p--){if(((r1=data[pix-=4])*0.3+(g1=data[pix1=pix+1])*0.59+(b1=data[pix2=pix+2])*0.11)>(data2[pix]*0.3+data2[pix1]*0.59+data2[pix2]*0.11)){data2[pix]=r1;data2[pix1]=g1;data2[pix2]=b1;}}
dataChanged=true;break;case"lineardodge":while(p--){if((r3=data[pix-=4]+data2[pix])>255)
data2[pix]=255;else
data2[pix]=r3;if((g3=data[pix1=pix+1]+data2[pix1])>255)
data2[pix1]=255;else
data2[pix1]=g3;if((b3=data[pix2=pix+2]+data2[pix2])>255)
data2[pix2]=255;else
data2[pix2]=b3;}
dataChanged=true;break;case"linearburn":while(p--){if((r3=data[pix-=4]+data2[pix])<255)
data2[pix]=0;else
data2[pix]=(r3-255);if((g3=data[pix1=pix+1]+data2[pix1])<255)
data2[pix1]=0;else
data2[pix1]=(g3-255);if((b3=data[pix2=pix+2]+data2[pix2])<255)
data2[pix2]=0;else
data2[pix2]=(b3-255);}
dataChanged=true;break;case"difference":while(p--){if((r3=data[pix-=4]-data2[pix])<0)
data2[pix]=-r3;else
data2[pix]=r3;if((g3=data[pix1=pix+1]-data2[pix1])<0)
data2[pix1]=-g3;else
data2[pix1]=g3;if((b3=data[pix2=pix+2]-data2[pix2])<0)
data2[pix2]=-b3;else
data2[pix2]=b3;}
dataChanged=true;break;case"screen":while(p--){data2[pix-=4]=(255-(((255-data2[pix])*(255-data[pix]))>>8));data2[pix1=pix+1]=(255-(((255-data2[pix1])*(255-data[pix1]))>>8));data2[pix2=pix+2]=(255-(((255-data2[pix2])*(255-data[pix2]))>>8));}
dataChanged=true;break;case"exclusion":var div_2_255=2/255;while(p--){data2[pix-=4]=(r1=data[pix])-(r1*div_2_255-1)*data2[pix];data2[pix1=pix+1]=(g1=data[pix1])-(g1*div_2_255-1)*data2[pix1];data2[pix2=pix+2]=(b1=data[pix2])-(b1*div_2_255-1)*data2[pix2];}
dataChanged=true;break;case"overlay":var div_2_255=2/255;while(p--){if((r1=data[pix-=4])<128)
data2[pix]=data2[pix]*r1*div_2_255;else
data2[pix]=255-(255-data2[pix])*(255-r1)*div_2_255;if((g1=data[pix1=pix+1])<128)
data2[pix1]=data2[pix1]*g1*div_2_255;else
data2[pix1]=255-(255-data2[pix1])*(255-g1)*div_2_255;if((b1=data[pix2=pix+2])<128)
data2[pix2]=data2[pix2]*b1*div_2_255;else
data2[pix2]=255-(255-data2[pix2])*(255-b1)*div_2_255;}
dataChanged=true;break;case"softlight":var div_2_255=2/255;while(p--){if((r1=data[pix-=4])<128)
data2[pix]=((data2[pix]>>1)+64)*r1*div_2_255;else
data2[pix]=255-(191-(data2[pix]>>1))*(255-r1)*div_2_255;if((g1=data[pix1=pix+1])<128)
data2[pix1]=((data2[pix1]>>1)+64)*g1*div_2_255;else
data2[pix1]=255-(191-(data2[pix1]>>1))*(255-g1)*div_2_255;if((b1=data[pix2=pix+2])<128)
data2[pix2]=((data2[pix2]>>1)+64)*b1*div_2_255;else
data2[pix2]=255-(191-(data2[pix2]>>1))*(255-b1)*div_2_255;}
dataChanged=true;break;case"hardlight":var div_2_255=2/255;while(p--){if((r2=data2[pix-=4])<128)
data2[pix]=data[pix]*r2*div_2_255;else
data2[pix]=255-(255-data[pix])*(255-r2)*div_2_255;if((g2=data2[pix1=pix+1])<128)
data2[pix1]=data[pix1]*g2*div_2_255;else
data2[pix1]=255-(255-data[pix1])*(255-g2)*div_2_255;if((b2=data2[pix2=pix+2])<128)
data2[pix2]=data[pix2]*b2*div_2_255;else
data2[pix2]=255-(255-data[pix2])*(255-b2)*div_2_255;}
dataChanged=true;break;case"colordodge":while(p--){if((r3=(data[pix-=4]<<8)/(255-(r2=data2[pix])))>255||r2==255)
data2[pix]=255;else
data2[pix]=r3;if((g3=(data[pix1=pix+1]<<8)/(255-(g2=data2[pix1])))>255||g2==255)
data2[pix1]=255;else
data2[pix1]=g3;if((b3=(data[pix2=pix+2]<<8)/(255-(b2=data2[pix2])))>255||b2==255)
data2[pix2]=255;else
data2[pix2]=b3;}
dataChanged=true;break;case"colorburn":while(p--){if((r3=255-((255-data[pix-=4])<<8)/data2[pix])<0||data2[pix]==0)
data2[pix]=0;else
data2[pix]=r3;if((g3=255-((255-data[pix1=pix+1])<<8)/data2[pix1])<0||data2[pix1]==0)
data2[pix1]=0;else
data2[pix1]=g3;if((b3=255-((255-data[pix2=pix+2])<<8)/data2[pix2])<0||data2[pix2]==0)
data2[pix2]=0;else
data2[pix2]=b3;}
dataChanged=true;break;case"linearlight":while(p--){if(((r3=2*(r2=data2[pix-=4])+data[pix]-256)<0)||(r2<128&&r3<0)){data2[pix]=0}else{if(r3>255)
data2[pix]=255;else
data2[pix]=r3;}
if(((g3=2*(g2=data2[pix1=pix+1])+data[pix1]-256)<0)||(g2<128&&g3<0)){data2[pix1]=0}else{if(g3>255)
data2[pix1]=255;else
data2[pix1]=g3;}
if(((b3=2*(b2=data2[pix2=pix+2])+data[pix2]-256)<0)||(b2<128&&b3<0)){data2[pix2]=0}else{if(b3>255)
data2[pix2]=255;else
data2[pix2]=b3;}}
dataChanged=true;break;case"vividlight":while(p--){if((r2=data2[pix-=4])<128){if(r2){if((r3=255-((255-data[pix])<<8)/(2*r2))<0)
data2[pix]=0;else
data2[pix]=r3}else{data2[pix]=0;}}else if((r3=(r4=2*r2-256))<255){if((r3=(data[pix]<<8)/(255-r4))>255)
data2[pix]=255;else
data2[pix]=r3;}else{if(r3<0)
data2[pix]=0;else
data2[pix]=r3}
if((g2=data2[pix1=pix+1])<128){if(g2){if((g3=255-((255-data[pix1])<<8)/(2*g2))<0)
data2[pix1]=0;else
data2[pix1]=g3;}else{data2[pix1]=0;}}else if((g3=(g4=2*g2-256))<255){if((g3=(data[pix1]<<8)/(255-g4))>255)
data2[pix1]=255;else
data2[pix1]=g3;}else{if(g3<0)
data2[pix1]=0;else
data2[pix1]=g3;}
if((b2=data2[pix2=pix+2])<128){if(b2){if((b3=255-((255-data[pix2])<<8)/(2*b2))<0)
data2[pix2]=0;else
data2[pix2]=b3;}else{data2[pix2]=0;}}else if((b3=(b4=2*b2-256))<255){if((b3=(data[pix2]<<8)/(255-b4))>255)
data2[pix2]=255;else
data2[pix2]=b3;}else{if(b3<0)
data2[pix2]=0;else
data2[pix2]=b3;}}
dataChanged=true;break;case"pinlight":while(p--){if((r2=data2[pix-=4])<128)
if((r1=data[pix])<(r4=2*r2))
data2[pix]=r1;else
data2[pix]=r4;else
if((r1=data[pix])>(r4=2*r2-256))
data2[pix]=r1;else
data2[pix]=r4;if((g2=data2[pix1=pix+1])<128)
if((g1=data[pix1])<(g4=2*g2))
data2[pix1]=g1;else
data2[pix1]=g4;else
if((g1=data[pix1])>(g4=2*g2-256))
data2[pix1]=g1;else
data2[pix1]=g4;if((r2=data2[pix2=pix+2])<128)
if((r1=data[pix2])<(r4=2*r2))
data2[pix2]=r1;else
data2[pix2]=r4;else
if((r1=data[pix2])>(r4=2*r2-256))
data2[pix2]=r1;else
data2[pix2]=r4;}
dataChanged=true;break;case"hardmix":while(p--){if((r2=data2[pix-=4])<128)
if(255-((255-data[pix])<<8)/(2*r2)<128||r2==0)
data2[pix]=0;else
data2[pix]=255;else if((r4=2*r2-256)<255&&(data[pix]<<8)/(255-r4)<128)
data2[pix]=0;else
data2[pix]=255;if((g2=data2[pix1=pix+1])<128)
if(255-((255-data[pix1])<<8)/(2*g2)<128||g2==0)
data2[pix1]=0;else
data2[pix1]=255;else if((g4=2*g2-256)<255&&(data[pix1]<<8)/(255-g4)<128)
data2[pix1]=0;else
data2[pix1]=255;if((b2=data2[pix2=pix+2])<128)
if(255-((255-data[pix2])<<8)/(2*b2)<128||b2==0)
data2[pix2]=0;else
data2[pix2]=255;else if((b4=2*b2-256)<255&&(data[pix2]<<8)/(255-b4)<128)
data2[pix2]=0;else
data2[pix2]=255;}
dataChanged=true;break;}
if(dataChanged)
otherCtx.putImageData(dataDesc2,0,0);if(amount!=1&&!Pixastic.Client.hasGlobalAlpha()){var p=w*h;var amount2=amount;var amount1=1-amount;while(p--){var pix=p*4;var r=(data[pix]*amount1+data2[pix]*amount2)>>0;var g=(data[pix+1]*amount1+data2[pix+1]*amount2)>>0;var b=(data[pix+2]*amount1+data2[pix+2]*amount2)>>0;data[pix]=r;data[pix+1]=g;data[pix+2]=b;}
params.useData=true;}else{var ctx=params.canvas.getContext("2d");ctx.save();ctx.globalAlpha=amount;ctx.drawImage(otherCanvas,0,0,rect.width,rect.height,rect.left,rect.top,rect.width,rect.height);ctx.globalAlpha=1;ctx.restore();}
return true;}},checkSupport:function(){return Pixastic.Client.hasCanvasImageData();}}
/* autogeneration */
define("lib/pixastic.custom", [], function(){});

/* @source  */;

define('mousetrap', 'lib/mousetrap.js');

require([
        'jquery',
        'jquery-caret',
        'jquery-atwho',
        'jquery-forms',
        'bootstrap',
        'lib/pixastic.custom',
        'mod/liveupdate',
        'mod/input-ext',
        'mod/quick_emoji',
        'mod/user_following',
        'mod/watch',
        //'mod/commit',  // delegate of .js-comment-edit-button // plz refac...
        'mod/diff',   // diff js
        'mod/user_profile_card',
        'mod/tasklist',
        'mod/mute',
        'mousetrap',
        'mod/pull_key',
    ],
    function ($, _, _, _, _, _, live, inputExt, quick_emoji, userFollowing) {
        $(function () {
            var channel_id = "code_pr_"+$('.discussion-tab-link').attr('data-url');
            var linecomment_channel_id = channel_id + 'linecomment';
            live.emit('ready', {channel: channel_id, msg: ''});
            $('textarea#new_comment_content').live(
                'keypress',
                (function (e) {
                    var username = $('textarea#new_comment_content').data('current-user');
                    live.emit('ready', {channel: channel_id, type: 'typing', username: username});
                })
            );

            // pull-nav
            var getAnchor = function (url) {
                var index = url.indexOf('#');
                if (index != -1) {
                    return url.substring(index + 1);
                }
                return '';
            };
            var loadTabContent = function (tab, isFirstLoad) {
                var container = $('#' + $(tab).attr('data-tab-container')),
                    url = $(tab).attr('data-j-url');

                if (container && container.children().length == 0) {
                    $('.loader').show();
                    container.load(url, {}, function () {
                        $('.loader').hide();
                        if (container.is('#discussion-pane') || container.is('#files-pane') || container.is("#commits-pane")) {
                            loadMergeGuide(container, function(st){
                                window.initState = st;
                            });

                            loadCommentInputExt();

                            $('#watch-ci').on('click', function(){
                                if ($(this).attr('checked')) {
                                    CINotification.init();
                                    window.ciWatcher = window.setInterval(function(){
                                        loadMergeGuide(container, function(st){
                                            var msg, prName = $('h2').text();
                                            if (st !== window.initState) {
                                                if (st === 'clean') {
                                                    msg = 'PR "'+ prName +'" can merge now';
                                                    clearTimeout(window.ciWatcher);
                                                } else if (st === 'error') {
                                                    msg = 'PR "'+ prName +'" occurred an error';
                                                    window.initState = 'error';
                                                } else if (st === 'dirty') {
                                                    msg = 'PR "'+ prName +'" got a qaci';
                                                    window.initState = 'dirty';
                                                } else {
                                                    msg = 'Something wrong... ping xutao!'
                                                }
                                                CINotification.create('Code need your Attention!', msg);
                                            }
                                        });
                                    }, 5000);
                                } else {
                                    clearTimeout(window.ciWatcher);
                                }
                            });

                        }
                        if (isFirstLoad) {
                            var anchor = getAnchor(location.href);
                            if (anchor !== '') {
                                var anchorEl = $(document.getElementById(anchor));
                                if (anchorEl.length > 0) {
                                    $('html, body').animate({scrollTop:anchorEl.offset().top}, 500);
                                }
                            }
                        }
                    });
                }
            };

            /* notification */
            var CINotification = {
                init: function () {
                    var webkitNotify = window.webkitNotifications,
                        notify = window.Notification;

                    if (webkitNotify) {
                        var st = webkitNotify.checkPermission();
                        if (st === 1) {
                            webkitNotify.requestPermission();
                        } else if (st === 2) {
                            alert('你拒绝了通知授权，请在通知设置里打开。')
                        }
                    } else if (notify && notify.permission !== "granted") {
                        notify.requestPermission(function (status) {
                            if (notify.permission !== status) {
                                notify.permission = status;
                            }
                        });
                    }
                },

                create: function(title,msg) {
                    var webkitNotify = window.webkitNotifications,
                        notify = window.Notification,
                        icon = '/static/img/code_lover.png';

                    if (webkitNotify) {
                        if (webkitNotify.checkPermission() != 0) {
                            message.init();
                        } else {
                            var n = webkitNotify.createNotification(icon,title, msg);
                            n.show();
                            /*
                            n.ondisplay = function() { };
                            n.onclose = function() { };
                            setTimeout(function(){n.cancle}, 5000);
                            */
                        }
                    } else if (notify) {
                        if (notify.permission == "granted") {
                            var n = new notify(title, { icon: icon, body: msg });
                        } else {
                            message.init();
                        }
                    }
                }
            }

            $('.pull-nav a[data-toggle="tab"]').on('show', function (e) {
                window.history.pushState('', '', $(e.target).attr('data-url'));
                loadTabContent($(e.target), false);
            });
            loadTabContent($('.pull-nav .active a'), true);
            var tabUrls = [], tabs = {};
            $('.pull-nav a[data-toggle="tab"]').each(
                function (i, t) {
                    var url = $(t).attr('data-url');
                    tabUrls.push(url);
                    tabs[url] = $(t);
                });
            $(window).bind(
                "popstate", function(e) {
                    var location = e.target.location,
                    path = location.href.split(location.protocol + '//' + location.host)[1],
                    anchorIndex = path.indexOf('#');
                    if (anchorIndex !== -1) {
                        path = path.substring(0, anchorIndex);
                    }
                    if (path) {
                        for (var i=0, l=tabUrls.length; i<l; i++) {
                            if (path === tabUrls[i]) {
                                tabs[tabUrls[i]].tab('show');
                                break;
                            }
                        }
                    }
                });

            // ticket-content-edit-form
            $('#ticket-content-edit-form').ajaxForm({
                dataType: 'json',
                delegation: true,
                success: function(r) {
                    if (r.r == '0') {
                        var ticket = $('#ticket');
                        ticket.find('h2').html(r.title_html);
                        ticket.find('.comment-content .comment-body').html(r.content_html);
                        // update ticket content in edit form
                        $('#ticket-content-edit-form').find('#issue_title').val(r.title);
                        $('#ticket-content-edit-form').find('#issue_body').val(r.content);
                    }
                    $('#ticket .comment-content').removeClass('is-comment-editing');
                }
            });

            // comment & linecomment edit
            $('body').delegate('.js-comment-edit-button', 'click', function (e) {
                var form_content = $(this).parents('.comment-header')
                .next('.comment-content')
                .children('.form-content');
                if (form_content != undefined) {
                    form_content.show().find('textarea').focus();
                    form_content.find('form.js-comment-update').ajaxForm({
                        dataType: 'json',
                        beforeSend: function() {
                            form_content.find('button[type="submit"]').attr('disabled', true).addClass('disabled')
                            .end().find('.loader').show();
                        },
                        success: function(r) {
                            if (r.r == 0 && r.html) {
                                if (form_content.find('textarea').attr('name') === 'pull_request_review_comment'){
                                    form_content.parents('.js-comments-holder').append(r.html);
                                    form_content.parents('.comment').remove();
                                } else {
                                    var comment = form_content.parents('.change');
                                    var avatar = comment.prev('.side-avatar');
                                    form_content.parents('#changelog').append(r.html);
                                    comment.remove();
                                    avatar.remove();
                                }
                            }
                            return true;
                        }
                    });
                } else {
                    return false;
                }
            });

            $('body').delegate('.form-content .comment-cancel-button', 'click', function (e) {
                var form_content = $(this).parents('.form-content');
                if (form_content != undefined) {
                    form_content.hide();
                } else {
                    return false;
                }
            });

            $('#discussion-pane').delegate('.comment-edit-button', 'click', function () {
                $('#ticket .comment-content').addClass('is-comment-editing').find('.form-content').show();
            });
            $('#discussion-pane').delegate('.comment-cancel-button', 'click', function () {
                $('#ticket .comment-content').removeClass('is-comment-editing');
            });

            $('#discussion-pane').delegate(
                '#fav-button', 'click', function (e) {
                    var btn = $(this),
                    data = {tid: btn.data('tid'),
                            tkind: btn.data('tkind')};
                    if (!btn.hasClass('faved')) {
                        $.post('/j/fav/', data,
                               function (r) {
                                   if (r.r == 0) {
                                       btn.addClass('faved');
                                   }
                               }, 'json');
                    } else {
                        $.ajax({url: '/j/fav/',
                                type: 'DELETE',
                                data: data,
                                dataType: 'json',
                                success: function(r) {
                                    if (r.r == 0) {
                                        btn.removeClass('faved');
                                    }
                                }
                               });
                    }
            });

            // diff_image
            $('#files-pane').delegate('#diff_image', 'click', function() {
                var imgid = $(this).attr("imgid");
                $("#org_image_div_"+imgid).hide();
                $("#diff_image_div_"+imgid).show();
                Pixastic.process(
                    document.getElementById("result_pic_"+imgid),
                    "blend",
                    {
                        mode: "difference",
                        image: $("#new_pic_"+imgid).get(0)
                    }
                );
            });
            $('#files-pane').delegate('#up_image', 'click', function(){
                var imgid = $(this).attr("imgid");
                $("#org_image_div_"+imgid).show();
                $("#diff_image_div_"+imgid).hide();
            });

            // pull files-pane patch toggle
            $('body').delegate('#files-pane #files div.meta', 'click', function(e){
                if (!$(e.target).parents('.actions').length > 0){
                    var inline = $(this).siblings('div .inline');
                    var side = $(this).siblings('div .side');
                    if (inline.css('display') === 'none' && side.css('display') === 'none'){
                        inline.show();
                        side.hide();
                    }else{
                        inline.hide();
                        side.hide();
                    }
               }
            });

            // merge guide
            var loadMergeGuide = function (container, cb) {
                if (!container)
                    return;
                var mergeGuide = container.find('#merge-guide');
                if (mergeGuide.length) {
                    var url = mergeGuide.attr('data-url');
                    mergeGuide.load(
                        url,
                        function () {
                            var mergeForm = mergeGuide.find('.merge-form'),
                            cancelBtn = mergeGuide.find('#merge-pr-cancel-btn');
                            mergeGuide.find('#merge-pr-confirm-btn').click(function () {
                                $(this).closest('.mergeable.clean').hide();
                                mergeForm.show();
                            });
                            cancelBtn.click(function () {
                                if (!$(this).hasClass('disabled')) {
                                    mergeForm.hide();
                                    mergeGuide.find('.mergeable.clean').show();
                                }
                            });
                            mergeForm.submit(function () {
                                $(this).find('button[type="submit"]').attr('disabled', true).addClass('disabled');
                                cancelBtn.addClass('disabled');
                                var username = $('textarea#new_comment_content').data('current-user');
                                live.emit('ready', {channel: channel_id, type: 'merge', username: username});
                                return true;
                            });

                            cb(container.find('.merge-branch').data('mst'));
                        }
                    );
                }
            };

            $('#discussion-pane').delegate('#add-comment-form #close', 'click', function () {
                var commentForm = $('#add-comment-form');
                if (commentForm.find('[name=comment_and_close]').length == 0) {
                    var input = $('<input>').attr('type', 'hidden').attr('name', 'comment_and_close').val('1');
                    commentForm.append(input);
                }
            });

            $('#discussion-pane').delegate('#add-comment-form #reopen', 'click', function () {
                var commentForm = $('#add-comment-form');
                if (commentForm.find('[name=comment_and_reopen]').length == 0) {
                    var input = $('<input>').attr('type', 'hidden').attr('name', 'comment_and_reopen').val('1');
                    commentForm.append(input);
                }
            });

            $('#discussion-pane').delegate('.outdated_mark', 'click', function () {
                $(this).toggle();
                $(this).next().toggle();
            });

            // delete pr comment
            $('#discussion-pane').delegate('.change-header .delete-pr-note-button', 'click', function (e) {
                if (!confirm('Are you sure you want to delete this?')) {
                    return false;
                }
                var comment = $(this).parents('.change');
                var avatar = comment.prev('.side-avatar');
                $.getJSON(
                    $(this).attr('href'),
                    function(r) {
                        if (r.r == '1'){
                            comment.remove();
                            avatar.remove();
                        }
                    }
                );
                return false;
            });

            $('#add-comment-form').ajaxForm({
                dataType: 'json',
                delegation: true,
                beforeSend: function () {
                    var commentForm = $('#add-comment-form');
                    commentForm.find('button[type="submit"]').attr('disabled', true).addClass('disabled')
                    .end().find('.loader').show();
                },
                success: function(r) {
                    var commentForm = $('#add-comment-form');
                    if (r.r == 0) {
                        if (r.reload && r.redirect_to) {
                            window.location.href = r.redirect_to;
                            return true;
                        } else if (r.html) {
                            commentForm.find('textarea').val('');
                            $('#changelog').append(r.html);
                            live.emit('ready', {channel: channel_id, msg:r.html});
                        }
                    } else if(r.error){
                        alert(r.error);
                    }
                    commentForm.removeClass('submitting').find('button[type="submit"]').attr('disabled', false)
                    .removeClass('disabled').end().find('.loader').hide();
                    return true;
                }
            });

            $('.tabnav-tabs a').live('click', function () {
                $(this).closest('.tabnav-tabs').find('a').removeClass('selected');
                $(this).addClass('selected');
            });

            $('.write-tab').live('click', function () {
                var form = $(this).closest('.previewable-comment-form');
                $(this).closest('.previewable-comment-form').removeClass('preview-selected').addClass('write-selected');
                form.find('#write_bucket').addClass('active').end().find('#preview_bucket').removeClass('active');
            });
            $('.preview-tab').live('click', function () {
                var form = $(this).closest('.previewable-comment-form');
                form.removeClass('write-selected').addClass('preview-selected');
                form.find('#write_bucket').removeClass('active').end().find('#preview_bucket').addClass('active');
                form.find('#preview_bucket p').html("Loading preview...");
                var url = form.find('#preview_bucket .content-body').data('api-url'),
                text = form.find('#write_bucket textarea').val();
                form.find('#preview_bucket .content-body').load(url, {text: text});
            });

            var loadCommentInputExt = function () {
                if ($('#participants').length > 0) {
                    var participants = JSON.parse($('#participants').val());
                    var teams = JSON.parse($('#all-teams').val() || '[]');
                    var following = userFollowing.val();
                    var users = $.unique(
                        participants.concat(following, teams)
                    );
                    $('textarea#new_comment_content, textarea#issue_body')
                        .atwho("@", {data:users, limit:7});
                }
                var newCommentInput = $('textarea#new_comment_content');
                inputExt.enableEmojiInput(newCommentInput);
                inputExt.enablePullsInput(newCommentInput);
                inputExt.shortcut2submit(newCommentInput);
                inputExt.enableZenMode(newCommentInput);
                inputExt.enableQuickQuotes(newCommentInput);

                var uploader = $('#form-file-upload'),
                    textarea = $('#add-comment-form').find('textarea');
                inputExt.enableUpload(uploader, textarea);

                $('#add-comment-form button[type="submit"]').tooltip();
            };
          loadCommentInputExt();

         });

        quick_emoji.enable('#new_comment_content');
    }
);
