#!/usr/bin/expect

set user $env(GIT_USER)

puts "User is: $user"
spawn git push origin master
expect -re "^Username.*"
send "$env(GIT_USER)"
expect -re "Password.*"
send "$env(GIT_PASSWORD)"
interact