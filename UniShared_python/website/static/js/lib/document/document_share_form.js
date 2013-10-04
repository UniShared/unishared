$(document).ready(function() {
    "use strict";
	if(!$.formShare) {
		$.formShare = {};
	}
	
    $("#form_share").validate({
        rules : {
            share_text : {
                required : function(element) {
                    return ($("#social_facebook").is(':checked') || $("#social_twitter").is(':checked'));
                },
                maxlength : 140
            }
        },
        errorPlacement : function(error, element) {
            $('.jMax-text').css('color', 'red');
        },
        success : function(label) {
            $('.jMax-text').css('color', '');
        },
        submitHandler : $.formShare.submitHandler
    });
    
	$.formShare.validate = function() {
		var values;

		var social_facebook = $("#social_facebook").is(':checked');
		if (social_facebook) {
			values = {};
			values.social_facebook = social_facebook;
		}

		var social_twitter = $("#social_twitter").is(':checked');
		if (social_twitter) {
			if (!values) {
				values = {};
			}

			values.social_twitter = social_twitter;
		}
		
		var message = $("#share_text").val();
        if (message && message.length > 0) {
            if (!values) {
                values = {};
            }

            values.message = message;
        }
		
        var form_success_handler = null;
        if ( typeof $.formShare.successHandler == 'function') {
            form_success_handler = $.formShare.successHandler;
        }

        var form_error_handler = null;
        if ( typeof $.formShare.errorHandler == 'function') {
            form_error_handler = $.formShare.errorHandler;
        }

		if (values) {
			var url = '/class/share/',
			resource_id = $('#resource_id').val();
			if (resource_id) {
				url += resource_id;
			}

			ajaxSend(url, 'post', values, form_success_handler, form_error_handler);
		}
		else {
           if ( typeof form_success_handler == 'function') {
            form_success_handler();
           }
		}

		return typeof values != "undefined";
	};
	
	$.formShare.checkUncheck = function (name) {
		$('#social_' + name).attr('checked', !$('#social_' + name).attr('checked'));
		if ($('#social_' + name).is(':checked')) {
			$('#social_' + name + '_picto_nb').hide();
			$('#social_' + name + '_picto_color').css('display', 'block');
		} else {
			$('#social_' + name + '_picto_color').hide();
			$('#social_' + name + '_picto_nb').css('display', 'block');
		}
	};
	
	$.formShare.clearSelected = function () {
		$('#social_facebook_picto_color').hide();
		$('#social_facebook_picto_nb').css('display', 'block');
		
		$('#social_twitter_picto_color').hide();
		$('#social_twitter_picto_nb').css('display', 'block');
	};
	
    $.formShare.shortenUrl = function(resource_id) {
        var document_url = location.protocol + "//" + location.hostname + (location.port && ":" + location.port) + "/class/" + resource_id;
        BitlyClient.shorten(document_url, function(data) {
            var bitly_link = null;
            for (var r in data.results) {
                bitly_link = data.results[r]['shortUrl'];
                break;
            };
            var base_url = 
            $("#share_text_container").maxinput({
                'position' : 'topleft',
                'showtext' : true,
                'defaultText' : bitly_link + ' via @UniShared'
            });
        });
    };
    
    $(window).on('unishared.resource_available', $.formShare.shortenUrl);

	fbEnsureInit(function() {
		FB.api({
			method : 'users.hasAppPermission',
			ext_perm : 'publish_stream'
		}, function(resp) {
			if (resp === "1") {
				$('#social_facebook_picto').addClass('facebook-active');
			}
		});
	});

	$('#social_facebook_picto').click(function(e) {
		if (!$(this).hasClass('facebook-active')) {
			fbEnsureInit(function() {
				FB.login(function() {
					FB.api({
						method : 'users.hasAppPermission',
						ext_perm : 'publish_stream'
					}, function(resp) {
						if (resp === "1") {
							if($.formShare && $.formShare.checkUncheck) {
								$.formShare.checkUncheck('facebook');
							}
							
							$('#social_facebook_picto').addClass('facebook-active');
						}
					})
				}, {
					scope : 'publish_stream'
				});
			});
		} else {
			if($.formShare && $.formShare.checkUncheck) {
				$.formShare.checkUncheck('facebook');
			}
		}

		e.preventDefault();
		return false;
	});
	
	var twitter = new function() {
		var that = this;
	
		this.startTwitterConnect = function(href) {
			var windowOptions = 'scrollbars=yes,resizable=yes,toolbar=no,location=yes';
			var width = 550;
			var height = 420;
			var winHeight = screen.height;
			var winWidth = screen.width;
		
			var left = Math.round((winWidth / 2) - (width / 2));
			var top = 0;
		
			if (winHeight > height) {
			top = Math.round((winHeight / 2) - (height / 2));
			}
		
			that._twitterWindow = window.open(href, 'twitterWindow', windowOptions + ',width=' + width + ',height=' + height + ',left=' + left + ',top=' + top);
			that._twitterInterval = window.setInterval(that.completeTwitterConnect, 1000);
		};
	
		this.completeTwitterConnect = function() {
			if (that._twitterWindow.closed) {
			window.clearInterval(that._twitterInterval);
			$('#social_twitter_picto').addClass('twitter-active');
				$.formShare.checkUncheck('twitter');
			}
		};
	};

	$('#social_twitter_picto').click(function(e) {
		if (!$(this).hasClass('twitter-active')) {
			twitter.startTwitterConnect($(this).attr('href'));
		}
		else {
			$.formShare.checkUncheck('twitter');
		}

		e.preventDefault();
		return false;
	});
});



