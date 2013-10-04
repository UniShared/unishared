"use strict";

require.config({
    baseUrl: window.staticUrl + 'js'
});

require(['lib/core', 'lib/validate'], function () {
    var login = (function() {
        "use strict";
        var $container_student_lifelonglearner, $container_school, $container_gmail, $container_gmail_title, $form_student, $form_school, $form_lifelonglearner, $form_gmail, $select_schools, $school, $is_student, $email, current_email;

        function init() {
            $container_student_lifelonglearner = $('#container_student_lifelonglearner');
            $container_school = $('#container_school');
            $container_gmail = $('#container_gmail');
            $container_gmail_title = $container_gmail.find('h2');
            $form_student = $('.form_student');
            $form_school = $("#form_school");
            $form_lifelonglearner = $('.form_lifelonglearner');
            $form_gmail = $("#form_gmail");
            $select_schools = $("#select_schools");
            $school = $("#school");
            $is_student = $("#is_student");
            $email = $("#email");
            current_email = $form_gmail.find('#current_email').val();

            $select_schools.change(function() {
                $school.val($(this).val());
            });

            if ($container_student_lifelonglearner.length) {
                $container_student_lifelonglearner.show();
            } else if ($container_school.length) {
                if (!$container_student_lifelonglearner.length) {
                    $container_school.find('.prev_button').hide();
                }
                $container_school.show();
            } else if ($container_gmail.length) {
                showGmailForm();
            }

            $form_student.click(goToSchoolForm);
            $form_lifelonglearner.click(goToGmailForm);

            $.validator.addMethod("regex_gmail", function(value, element) {
                var regexp = new RegExp(/^(([a-z0-9!\#$%&\\\'*+/=?^_`{|}~-]+\.?)*[a-z0-9!\#$%&\\\'*+/=?^_`{|}~-]+)@gmail\.com$/);

                if (regexp.constructor !== RegExp) {
                    regexp = new RegExp(regexp);
                } else if (regexp.global) {
                    regexp.lastIndex = 0;
                }

                return this.optional(element) || regexp.test(value);
            }, "erreur expression reguliere");

            $form_school.validate({
                onkeyup : true,
                rules : {
                    school : {
                        required : true
                    }
                },
                errorClass : "invalid",
                validClass : "success",
                errorPlacement : function(error, element) {
                },
                submitHandler : function() {
                    if ($container_gmail.length) {
                        $container_school.fadeOut(500, function() {
                            showGmailForm();
                        });
                    } else {
                        saveValues();
                    }
                }
            });

            $form_gmail.validate({
                onkeyup : true,
                rules : {
                    email : {
                        required : true,
                        email : true
                    }
                },
                errorClass : "invalid",
                validClass : "success",
                errorPlacement : function(error, element) {
                },
                success : function(label) {
                    $form_gmail.find("input:submit").css('background-color', '#C3FF75');
                },
                submitHandler : function() {
                    saveValues();
                }
            });

            $container_school.find('.prev_button').click(function() {
                if ($container_student_lifelonglearner.length) {
                    $container_school.fadeOut(500, function() {
                        $container_student_lifelonglearner.fadeIn(500);
                    });
                }
            });

            $container_gmail.find('.prev_button').click(function() {
                if ($is_student.val() === 'true') {
                    if ($container_school.length) {
                        $container_gmail.fadeOut(500, function() {
                            $container_school.fadeIn(500);
                        });
                    }
                } else {
                    if ($container_student_lifelonglearner.length) {
                        $container_gmail.fadeOut(500, function() {
                            $container_student_lifelonglearner.fadeIn(500);
                        });
                    }
                }
            });

        }

        /**
         * Save form values by calling the profile service (POST method)
         */
        function saveValues() {
            $('.loading').show();
            $('#overlay').show();

            var values;

            if ($is_student.val()) {
                if (!values) {
                    values = {};
                }
                values.is_student = $is_student.val();

                if ($is_student.val() === 'true') {
                    if ($school.val()) {
                        if (!values) {
                            values = {};
                        }
                        values.school = $school.val();
                    }
                }
            }

            if ($email.val()) {
                if (!values) {
                    values = {};
                }
                values.email = $email.val();
            }

            ajaxSend('/login/', 'post', values, function(data) {
                if (!data.success) {
                    $('.loading').hide();
                    $('#overlay').hide();

                    if (!data.email.success) {
                        $('#container .alert').text(data.email.message);
                        $('#container .alert').first().show();
                    }
                } else {
                    if(window.location.href.indexOf('settings') > -1) {
                        window.location.href = '/profile';
                    }
                    else {
                        window.location.reload();
                    }

                }
            }, function(data) {
                $('.loading').hide();
                $('#overlay').hide();

                if (data.error === 500) {
                    $('.next_button,.prev_button').hide();
                    $('#container .alert').first().show();
                }
            });
        }

        function backToClassTitle() {
            if ($container_school.is(':visible')) {
                $container_school.fadeOut(500, function() {
                    $container_student_lifelonglearner.fadeIn(500);
                });
            } else {
                if ($container_gmail.is(':visible')) {
                    $container_gmail.fadeOut(500, function() {
                        $container_student_lifelonglearner.fadeIn(500);
                    });
                }
            }

            $('.next_button,.prev_button').show();
            $('#container .alert').first().hide();
        }

        function showGmailForm() {
            $email.removeClass('invalid').removeClass('success');

            if ($is_student.val() === 'true') {
                $container_gmail_title.text('Please provide a Google email (Gmail or Google apps) to enjoy the best Unishared experience');
            } else {
                $container_gmail_title.text('Please verify your email to enjoy the best Unishared experience');
            }

            $email.val(current_email);
            $email.addClass('success');

            if (!$container_student_lifelonglearner.length && !$container_school.length) {
                $container_gmail.find('.prev_button').hide();
            }

            $container_gmail.fadeIn(500);
        }

        function goToGmailForm() {
            $is_student.val('false');

            if ($container_gmail.length) {
                $container_student_lifelonglearner.fadeOut(500, function() {
                    showGmailForm();
                });
            } else {
                saveValues();
            }
        }

        function goToSchoolForm() {
            $is_student.val('true');

            if ($container_school.length) {
                if ($select_schools.children().length) {
                    $school.val($select_schools.children(":first").val());
                }

                $container_student_lifelonglearner.fadeOut(500, function() {
                    $container_school.fadeIn(500);
                });
            }
        }

        return {
            "init" : init,
            "goToSchoolForm" : goToSchoolForm,
            "goToGmailForm": goToGmailForm
        }
    })();

    login.init();
});


