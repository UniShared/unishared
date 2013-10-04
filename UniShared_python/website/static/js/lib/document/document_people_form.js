$(document).ready(function() {
    "use strict";

    var $containerPeople = $('#container_people');
	if(!$.formPeople) {
		$.formPeople = {};
	}

    $.formPeople._role = null;

    $.formPeople.getRole = function() {
        return $.formPeople._role;
    }

    $.formPeople.setRole = function(role) {
        if(role) {
            $.formPeople._role = role;
            $containerPeople.find('.people-role').text(role);
        }
    }
	
	$.formPeople.addEmail = function (element) {
		if (element.valid()) {
			var $containerPeopleAlert = $containerPeople.find('.alert');
			if($('#people_emails_list li span:contains("' + element.val() + '")').length) {
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
	
	$("#form_people").validate({
		rules : {
			people_emails : {
				multiemail : true
			}
		},
		errorClass : "invalid",
		errorPlacement : function(error, element) {},
		submitHandler : $.formPeople.submitHandler
	});
	
	$.formPeople.validate = function() {
		var values;

		var people_facebook_ids = $("#form_people").find("#people_facebook_ids").val();
		if (people_facebook_ids) {
			values = {};
			values.people_facebook_ids = people_facebook_ids;
		}

		var people_emails = $('#people_emails_list').find('li span').map(function() {
			return $(this).text();
		}).get().join(',');
		if (people_emails.length) {
			if (!values) {
				values = {};
			}
			values.people_emails = people_emails;
		}

        var form_success_handler = null;
        if ( typeof $.formPeople.successHandler == 'function') {
            form_success_handler = $.formPeople.successHandler;
        }

        var form_error_handler = null;
        if ( typeof $.formPeople.errorHandler == 'function') {
            form_error_handler = $.formPeople.errorHandler;
        }

		if (values) {
			var resource_id = $('#resource_id').val();
			var url = '/notes/' + $.formPeople.getRole() + '/';

			if (resource_id) {
				url += resource_id;
			}

			ajaxSend(url, 'post', values, form_success_handler, form_error_handler);
		}
		else {
           if (typeof form_success_handler == 'function') {
            form_success_handler();
           }
        }

		return typeof values != "undefined";
	}
	
	fbEnsureInit(function() {
		var $jfmfsContainer = $("#jfmfs-container");
		
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
				$.formPeople.clearSelected = function() {
					var jfmfs = $("#jfmfs-container").data('jfmfs');
					jfmfs.clearSelected();
					jfmfs.resetFilter();
                    var $peopleEmailsList = $('#people_emails_list');
					$peopleEmailsList.find('li').remove();
                    $peopleEmailsList.find('input').val('').removeClass('valid invalid');
				}

				$jfmfsContainer.show();
			}); 
		}
		
		$jfmfsContainer.show();
	});

	$('#form_people').find('.icon-plus-sign').click(function (event) {
		$.formPeople.addEmail($('#people_emails'));
		event.preventDefault();
		return false;
	});
	
	$('#people_emails').keypress(function(event) {
		var keycode = (event.keyCode ? event.keyCode : event.which);
		if (keycode == '13') {
			$.formPeople.addEmail($(this));
			event.preventDefault();
			return false;
		}

	});
});