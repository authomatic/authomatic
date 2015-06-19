#!/usr/bin/expect

set user $env(GIT_USER)
set password $env(GIT_PASSWORD)

puts "User is: $user"
puts "Password hash is: $env(GIT_PASSWORD_HASH)"

spawn git push origin master
expect -re "^Username.*"
send "$env(GIT_USER)\r"
expect -re "Password.*"
send "$password\r"
interact