// the semi-colon before function invocation is a safety net against concatenated
// scripts and/or other plugins which may not be closed properly.
;(function ( $, window, document, undefined ) {
    if (!$.unishared) {
        $.unishared = {};
    };

    // undefined is used here as the undefined global variable in ECMAScript 3 is
    // mutable (ie. it can be changed by someone else). undefined isn't really being
    // passed in so we can ensure the value of it is truly undefined. In ES5, undefined
    // can no longer be modified.

    // window and document are passed through as local variable rather than global
    // as this (slightly) quickens the resolution process and can be more efficiently
    // minified (especially when both are regularly referenced in your plugin).

    // Create the defaults once
    var pluginName = "popup",
        defaults = {
            propertyName: "value"
        };

    // The actual plugin constructor
    function Popup( element, options ) {
        this.$element = $(element);

        // jQuery has an extend method which merges the contents of two or
        // more objects, storing the result in the first object. The first object
        // is generally empty as we don't want to alter the default options for
        // future instances of the plugin
        this.options = $.extend( {}, defaults, options );

        this._defaults = defaults;
        this._name = pluginName;

        this.init();
    }

    Popup.prototype = {

        init: function() {
            // Place initialization logic here
            // You already have access to the DOM element and
            // the options via the instance, e.g. this.element
            // and this.options
            // you can add more functions like the one below and
            // call them like so: this.yourOtherFunction(this.element, this.options).
            this.$overlay = $('#overlay');

            this.$element.find('.prev_button').click($.proxy(this.close, this));

            $(document).click($.proxy(function (e) {
                var click = $(e.target), outsideDiv = $("#overlay div:first").parents();

                if (click.is(outsideDiv)) {
                    this.close();
                }
            }, this));
        },

        show: function () {
            this.$overlay.fadeIn(500);
            this.$element.show();
        },

        close: function() {
            this.$overlay.fadeOut(500);
            this.$element.hide();
        }
    };

    // A really lightweight plugin wrapper around the constructor,
    // preventing against multiple instantiations
    $.fn['unishared_' + pluginName] = function ( methodOrOptions ) {
        return this.each(function () {
            var data = $.data(this, "plugin_" + pluginName);

            if (data && data[methodOrOptions] ) {
                return data[ methodOrOptions ].apply( data, Array.prototype.slice.call( arguments, 1 ));
            } else if ( typeof methodOrOptions === 'object' || ! methodOrOptions ) {
                // Default to "init"
                $data = $.data(this, "plugin_" + pluginName, new Popup( this, methodOrOptions ));
            } else {
                $.error( 'Method ' +  methodOrOptions + ' does not exist on ' + pluginName );
            }
        });
    };

})( jQuery, window, document );