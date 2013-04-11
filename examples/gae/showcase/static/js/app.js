$(document).ready(function (e) {
	
	authomatic.accessDefaults.backend = 'http://authomatic.com:8080/login/';
	
	authomatic.popup();
	
	var s = authomatic.format('x {user.id} x {user.name} x {pokus} x', {user:{"id": 123, name: 'hudo'}, pokus: 'keket'});
	console.log(s);
	
	$pokus = $('#pokus');
	
	// pokus();
	
	$('form.api-post').submit(function(e) {
		e.preventDefault();
		var message = $(e.target).find('input[name=message]').val();
		console.log('message:', message);
	});
	
	// disable empty form
	
	window.loginCallback = function(result){
		if(result.user){
			
			console.log('credentials:', result.user.credentials);
			
			$pokus.click(function (e) {
				e.preventDefault();
				$.fn.authomatic.access(result.user.credentials, 'https://example.com');
			});
			
			$('#error').slideUp(1000, function () {
				
				console.log('LOGIN RESULT:', result);
				
				var jsonParam = {
					"credentials": result.user.credentials,
					"url": "https://example.com",
					"method": "POST" 
				};
				
				var testURL = 'login/?json=' + encodeURIComponent(JSON.stringify(jsonParam));
				$('#test').attr('href', testURL);
				
				var $userData = $('#user-data');
				
				$('#user-name').html(result.user.name);
				$('#user-id').html(result.user.id);
				$('#user-email').html(result.user.email);
				$('#user-picture').attr('src', result.user.picture);
				$userData.html(JSON.stringify(result.user.data, undefined, 4));
				$('#user-provider').html(result.provider.name);
				$('#user').slideDown(2000);
				
				if(result.custom.apis){
					$apis = $('#user-apis');
					$apis.empty();
					
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
						
						if (method == 'GET'){
							$form.append('<input type="submit" class="button radius" value="' + title + '" />');
						} else if (method == 'POST'){
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
						}
						
						$form.submit(function(e){
							e.preventDefault();
							var $form = $(e.target);
							var url = $form.attr('action');
							var method = $form.attr('method');
							var message = $form.find('input[name=message]').val();
							
							$userData.slideUp('fast', function(){
								$('#user-data-loader').slideDown('fast');
							});
							
							authomatic.access(result.user.credentials, url, {
								method: method,
								substitute: {message: message, user: result.user},
								success: function(data){
									$userData.html(JSON.stringify(data, undefined, 4));
								},
								complete: function(jqXHR, status){
									$('#user-data-loader').slideUp('fast', function(){
										if(status == 'error'){
											$userData.html(jqXHR.responseText);
										}
										$userData.slideDown('fast');
									});
								}
							})
						});
						
						$apis.append($form);
					}
				}
				
			});
		}else if(result.error){
			$('#user').slideUp(2000, function () {
				$('#error-message').html(result.error.message);
				$('#error').slideDown(1000);
			});
		}
	};
});