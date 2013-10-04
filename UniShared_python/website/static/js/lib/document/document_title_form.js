"use strict";

define([
        '../search_panel',
        '../core',
        'lib/jquery-ui-timepicker-addon',
        'lib/jquery-ui-sliderAccess'
    ],
    function(SearchPanel) {
        SearchPanel.attachTo('.search-panel', {placeHolder: "Type your notes' name", autoComplete:true, titleOnly:true});

        if(!$.formTitle) {
            $.formTitle = {};
        }

        $.formTitle.successHandler = function(data) {
            if (data && data.resource_id) {
                $('#resource_id').val(data.resource_id);

                $(window).trigger('unishared.resource_available', data.resource_id);
            }
        };

        $.formTitle.submitHandler = function() {
                $("#form_document_title").find('.next_button').trigger('submit');

                var values;

                var document_title = $('.search-panel .search-field').val();
                if(document_title) {
                    values = {};
                    values.document_title = document_title;
                }

                var from = getUrlVars().from;
                if(from) {
                    if(!values) {
                        values = {};
                    }
                    values.from = from;
                }

                var starting_now = $('input:radio[name="starting_now"]:checked').val();
                if (starting_now == "0") {
                    if (!values) {
                        values = {};
                    }
                    values.starting_now = starting_now;
                    values.starting_time = $('#starting_time').val();
                    values.create_facebook_event = $('#create_facebook_event').is(':checked');
                }

                if(values) {
                    ajaxSend('/notes/create/', 'post',values, $.formTitle.successHandler, $.formTitle.errorHandler);
                }
        };

        $.formTitle.showCalendar = function () {
            if (!$('#datetimepicker.hasDatepicker').length) {
                var nowPlusOneHour = new Date();
                nowPlusOneHour.addMinutes(60);
                $('#datetimepicker').datetimepicker({
                    minDateTime : nowPlusOneHour,
                    showButtonPanel : false,
                    timeFormat : "hh:mm",
                    useLocalTimezone : true,
                    altField : "#starting_time",
                    altFieldTimeOnly : false,
                    altFormat : $.datepicker.ISO_8601,
                    altSeparator : "T",
                    altTimeFormat : 'hh:mm:00z',
                    timezoneIso8601 : true
                });
            } else {
                $('#datetimepicker').show();
            }
            $('#create_facebook_event_container').show();
        };

        $("#form_document_title").validate({
            onfocusout : function(element) {
                $(element).valid();
            },
            rules : {
                searchField : {
                    required : true,
                    maxlength : 150
                }
            },
            errorClass : "invalid",
            validClass : "success",
            errorPlacement : function(error, element) {},
            submitHandler : $.formTitle.submitHandler
        });

        $.formTitle.showCalendar();

        $('#starting_now_yes').click(function(e) {
            $('#datetimepicker').hide();
            $('#create_facebook_event_container').hide();
        });

        $('#starting_now_no').click(function(e) {
            $.formTitle.showCalendar();
        });

        $('#create_facebook_event').click(function(e) {
            if (!$(this).hasClass('permission-ok')) {
                fbEnsureInit(function() {
                    FB.login(function() {
                        FB.api({
                            method : 'users.hasAppPermission',
                            ext_perm : 'create_event'
                        }, function(resp) {
                            if (resp == "1") {
                                $('#create_facebook_event').attr('checked', 'checked');
                                $('#create_facebook_event').addClass('permission-ok');
                            }
                        })
                    }, {
                        scope : 'create_event'
                    });
                });
            }
        });
});