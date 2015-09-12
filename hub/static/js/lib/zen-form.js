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
