;!function ($) {
    "use strict";

    var HubNameForm = function (element, options) {
        this.init(element, options);
    }

    HubNameForm.prototype = {
        constructor: HubNameForm,

        init: function (element, options) {
            this.$element = $(element);
            this.options = this.getOptions(options);
            this.successHandler = options.successHandler;
            this.errorHandler = options.errorHandler;

            this.$element.find('form').validate({
                onfocusout: function (element) {
                    $(element).valid();
                },
                rules: {
                    hub_name: {
                        required: true,
                        minlength: 3,
                        maxlength: 15,
                        accept: "[a-z0-9_-]"
                    }
                },
                errorClass: "invalid",
                validClass: "success",
                errorPlacement: function (error, element) {
                },
                submitHandler: this.submitHandler
            });
        },

        getOptions: function (options) {
            options = $.extend({}, $.fn.hubNameForm.defaults, options, this.$element.data())

            if (options.delay && typeof options.delay == 'number') {
                options.delay = {
                    show: options.delay, hide: options.delay
                }
            }

            return options;
        },

        submitHandler: function (element) {
            var values, $hubNameForm, hub_name;

            $hubNameForm = $(element).closest('#container_hub_name');
            hub_name = $hubNameForm.find('#hub_name').val();
            if (hub_name) {
                if (!values) {
                    values = {};
                }

                values.hub_name = hub_name;
            }

            $hubNameForm.trigger('hub-name-form-submit');

            if (values) {
                var successHandler = $hubNameForm.data('hubNameForm').successHandler;
                var errorHandler = $hubNameForm.data('hubNameForm').errorHandler;

                ajaxSend('/hubs/create/', 'post', values, successHandler, errorHandler);
            }
        }
    };

    $.fn.hubNameForm = function (option) {
        return this.each(function () {
            var $this = $(this)
                , data = $this.data('hubNameForm')
                , options = typeof option == 'object' && option
            if (!data) $this.data('hubNameForm', (data = new HubNameForm(this, options)))
            if (typeof option == 'string') data[option]()
        })
    }

    $.fn.hubNameForm.Constructor = HubNameForm;

    $.fn.hubNameForm.defaults = {
        'successHandler': null,
        'errorHandler': null
    }

}(window.jQuery);