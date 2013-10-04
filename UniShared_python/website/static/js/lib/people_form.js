define(
    [
        './components/component',
        './jfmfs',
        './mustache',
        './core',
        './validate'
    ],

    function(defineComponent, jfmfs, Mustache)  {

        return defineComponent(peopleForm);

        function peopleForm() {
            this.defaultAttrs({
                container: '#overlay',
                role: null,
                canClose: true,
                type: null,
                resourceId: null,
                alert: '.alert',
                peopleFacebookIdsField : '#people_facebook_ids',
                peopleEmailsField: '#people_emails_list',
                emailField: '#people_emails',
                iconEmailPlusSign: '.icon-plus-sign',
                jfmfsContainer: '#jfmfs-container',
                peopleRole: '.people-role',
                submitLabel: null
            });

            this.after('initialize', function() {
                $.validator.addMethod("multiemail", function(value, element) {
                    if (this.optional(element))// return true on optional element
                        return true;
                    var emails = value.trim().split(new RegExp("\\s*,\\s*", "gi"));
                    var valid = true;
                    for (var i in emails) {
                        value = emails[i].trim();
                        valid = valid && jQuery.validator.methods.email.call(this, value, element);
                    }
                    return valid;
                });

                this.$node.find('form').validate({
                    rules : {
                        people_emails : {
                            multiemail : true
                        }
                    },
                    errorClass : "invalid",
                    errorPlacement : function(error, element) {},
                    submitHandler : $.proxy(this.validate, this)
                });

                var $iconEmailPlusSign = this.select('iconEmailPlusSign');
                this.on($iconEmailPlusSign, 'click', this.addEmail);

                this.on(this.select('peopleEmailsField'), 'keypress', function(event) {
                    var keycode = (event.keyCode ? event.keyCode : event.which);
                    if (keycode == '13') {
                        this.addEmail();
                        event.preventDefault();
                        return false;
                    }
                });

                this.on('show', this.show);
                this.on('setRole', function(event, params) {
                    $.extend(this.attr,params);
                    this.setRole();
                });

                this.setRole();
                this.setSubmitLabel();

                if(this.attr.canClose) {
                    var proxyHide = $.proxy(this.hide, this);
                    this.on('hide', proxyHide);
                    this.$node.find('.close').show().click($.proxy(this.close, this));
                    this.$node.find('.prev_button').hide();
                }


                fbEnsureInit($.proxy(this.initJfmfsContainer, this));
            });

            this.initJfmfsContainer = function() {
                var $jfmfsContainer = this.select('jfmfsContainer');

                if (!$jfmfsContainer.find('#jfmfs-friend-selector').length) {
                    $jfmfsContainer.jfmfs({
                        labels: {
                            selected: "Selected",
                            filter_default: "Start typing a name",
                            filter_title: "Or find friends:",
                            all: "All",
                            max_selected_message: "{0} of {1} selected"
                            // message to display showing how many items are already selected like: "{0} of {1} chosen"
                        },
                        exclude_friends:$('.co_writers ul li').map(function () { return $(this).attr('facebook-id') }).get()});
                    var $jfmfsFriendSelector = $jfmfsContainer.find('#jfmfs-friend-selector');

                    $jfmfsContainer.bind("jfmfs.selection.changed", function(e, data) {
                        var selectedIds = [];
                        for (var i in data) {
                            selectedIds.push(data[i].id);
                        }
                        $('#people_facebook_ids').val(selectedIds.join(','));
                    });

                    $jfmfsContainer.bind("jfmfs.friendload.finished", function() {
                        $jfmfsContainer.show();
                    });
                }
            }

            this.addEmail = function () {
                var element = $(this.select('emailField'));

                if (element.val().length && element.valid()) {
                    var $containerPeopleAlert = this.select(this.attr.alert);
                    if(this.select('peopleEmailsField').find('li span:contains("' + element.val() + '")').length) {
                        $containerPeopleAlert.text('Co-writer with this email is already invited');
                        $containerPeopleAlert.show();
                    }
                    else {
                        $containerPeopleAlert.hide();

                        var emails = element.val().split(',');

                        for(var i in emails) {
                            var $liEmail = $(Mustache.render('<li class="label"><i class="icon-remove pull-right"></i><span>{{email}}</span></li>', {'email' : emails[i].trim()}));
                            $liEmail.find('.icon-remove').click(function() {
                                $(this).closest('.label').remove();
                            });
                            $liEmail.insertBefore($('#people_emails_list').find('input'));
                        }

                        element.val('');
                    }
                }
            }

            this.clearSelected = function() {
                var jfmfs = this.select('jfmfsContainer').data('jfmfs');
                jfmfs.clearSelected();
                jfmfs.resetFilter();
                var $peopleEmailsList = $('#people_emails_list');
                $peopleEmailsList.find('li').remove();
                $peopleEmailsList.find('input').val('').removeClass('valid invalid');
                this.select('peopleFacebookIdsField').val('');
            }

            this.validate = function() {
                var values,
                $alert = this.select('alert');

                this.trigger('submit');
                $alert.hide();

                var people_facebook_ids = this.select('peopleFacebookIdsField').val();
                if (people_facebook_ids) {
                    values = {};
                    values.people_facebook_ids = people_facebook_ids;
                }

                var people_emails = this.select('peopleEmailsField').find('li span').map(function() {
                    return $(this).text();
                }).get().join(',');
                if (people_emails.length) {
                    if (!values) {
                        values = {};
                    }
                    values.people_emails = people_emails;
                }

                var cowriters = getUrlVars()['cowriters'];
                if(cowriters) {
                    if (!values) {
                        values = {};
                    }
                    values.cowriters = cowriters
                }

                if (values) {
                    var resource_id = this.resourceId;
                    var url = '/' + this.attr.type + '/' + this.attr.role + '/' + this.attr.resourceId;

                    if (resource_id) {
                        url += resource_id;
                    }

                    ajaxSend(url, 'post', values, $.proxy(this.successHandler, this), $.proxy(this.errorHandler, this));
                }
                else {
                    if (this.attr.canClose) {
                        $alert.text('Please select at least one friend or enter one email');
                        $alert.show();
                    }
                    else {
                        this.successHandler();
                    }
                }
            }

            this.setRole = function () {
                this.select('peopleRole').text(this.attr.role);
            }

            this.setSubmitLabel = function () {
                this.$node.find('.btn-success').text(this.attr.submitLabel);
            }

            this.show = function () {
                this.$node.show();
                this.select('jfmfsContainer').show();
                this.clearSelected();

                if(_gaq) {
                    _gaq.push(['_trackEvent', this.attr.type, 'Invite ' + this.attr.role]);
                }
            }

            this.close = function () {
                this.trigger('hide');
                this.hide();
            }

            this.hide = function () {
                this.$node.hide();
            }

            this.successHandler = function (data) {
                this.trigger('success', data);
            }

            this.errorHandler = function (data) {
                this.trigger('error', data);
            }
        }
    }
);