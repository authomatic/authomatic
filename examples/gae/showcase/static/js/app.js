$(document).ready(function (e) {
	var $user = $('#user');
	var $error = $('#error');
	var $userPicture = $('#user-picture');
	
	$('form.persona').on('click', function(e){
		e.preventDefault();
		alert('Mozilla Persona is not implemented yet!');
	});
	
	authomatic.setup({
		// Called when the popup gets open.
		onPopupOpen: function(url) {
			// Track the event in Google analytics
			_gaq.push(['_trackEvent', 'Login Buttons', 'Click', url]);
			
			$user.slideUp(1500);
			$error.slideUp('fast');
			$userPicture.fadeOut();
		},
		// Called when the login procedure is over.
		onLoginComplete: function(result) {
			if(result.user) {
				// Populate user info with data from login result
				$('#user-name').html(result.user.name);
				$('#user-id').html(result.user.id);
				$('#user-email').html(result.user.email);
				$('#user-provider').html(result.provider.name);
				$user.slideDown(1500, function(e) {
					if(result.user.picture) {
						$userPicture.attr('src', result.user.picture);
						$userPicture.fadeIn();
					}
				});
				
				var $userData = $('#user-data');
				$userData.html(JSON.stringify(result.user.data, undefined, 4));
				
				// Check if there are APIs that we passed to the result.custom object
				// through LoginResult.js_callback() in the login handler.
				if(result.custom.apis){
					// Select the APIs container and delete APIs from previous logins.
					$apis = $('#user-apis');
					$apis.empty();
					
					// Populate the container with API forms.
					for (var i in result.custom.apis){
						var title = i
						var api = result.custom.apis[i];
						var method = api[0];
						var url = api[1];
						var placeholder = api[2];
						var defaultValue = api[3];
						
						var $form = $('<form />');
						$form.attr('action', url);
						$form.attr('method', method);
						
						if (placeholder){
							// Form with input field.
							var formHTML = [
								'<div class="row collapse">',
									'<div class="large-7 small-8 columns">',
										'<input type="text" name="message" placeholder="' + placeholder + '" value="' + defaultValue + '">',
									'</div>',
									'<div class="large-5 small-4 columns">',
										'<input type="submit" class="button postfix radius" value="' + title + '" />',
									'</div>',
								'</div>'
							].join('');
								
							$form.append(formHTML);
						} else {
							// Form with just the submit button.
							$form.append('<input type="submit" class="button radius" value="' + title + '" />');
						}
						
						// Add behavior to the form.
						$form.submit(function(e){
							e.preventDefault();
							var $form = $(e.target);
							var url = $form.attr('action');
							var method = $form.attr('method');
							var message = $form.find('input[name=message]').val();
							
							// Show loader
							$userData.slideUp('fast', function(){
								$('#user-data-loader').slideDown('fast');
							});
							
							// Access protected resource
							authomatic.access(result.user.credentials, url, {
								method: method,
								substitute: {message: message, user: result.user},
								onAccessSuccess: function(data){
									// Called only on success.
									var niceData = JSON.stringify(data, undefined, 4);
									$userData.html(niceData);
								},
								onAccessComplete: function(jqXHR, status){
									// Allways called.
									$('#user-data-loader').slideUp('fast', function(){
										if(status == 'error'){
											$userData.html(jqXHR.responseText);
										}
										$userData.slideDown('fast');
									});
								}
							})
						});
						
						// Append the form to container.
						$apis.append($form);
					}
				}
			} else if (result.error) {
				$('#user').slideUp('fast', function () {
					$('#error-message').html(result.error.message);
					$error.slideDown('fast');
				});
			}
		}
	});
	
	authomatic.popupInit();
});