#!/usr/bin/env python

import urllib
import urllib2
import cookielib
import ConfigParser

config = ConfigParser.ConfigParser()
config.read('config.ini')

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
login_data = urllib.urlencode({
        'ctusername' : config.get("login", "username"),
        'ctpassword' : config.get("login", "password"),
        'browserversion': "ns6",
        'activex': "False",
        'useraction': "login",
})

h1 = opener.open('https://currenttime.bouvet.no/login.asp', login_data).read()



