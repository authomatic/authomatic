import httplib



# print urlopen('https://authomatic.com:8080', context=ctx).read()

connection = httplib.HTTPSConnection('authomatic.com', 8080)

connection.request('GET', '/')

response = connection.getresponse()

print response.status
print response.read()
