#!/usr/bin/expect

spawn git push
expect -re "^Username.*"
send "$env(GIT_USER)\r"
expect -re "Password.*"
send "$env(GIT_PASSWORD)\r"
interact