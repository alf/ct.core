#!/usr/bin/env python

from lxml import html
import datetime
import urllib
import urllib2
import cookielib
import ConfigParser

class CurrentTime(object):
    def __init__(self):
        self._browser = self.login()
        self._page = self._get_entire_month()

    def login(self):
        browser = self._create_browser()
        config = ConfigParser.ConfigParser()
        config.read('config.ini')
    
        login_data = urllib.urlencode({
                'ctusername' : config.get("login", "username"),
                'ctpassword' : config.get("login", "password"),
                'browserversion': "ns6",
                'activex': "False",
                'useraction': "login",
                })
    
        browser.open('https://currenttime.bouvet.no/login.asp', login_data)
        return browser
    
    def _create_browser(self):
        cj = cookielib.CookieJar()
        return urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    def _get_entire_month(self):
        response = self._browser.open('https://currenttime.bouvet.no/Timesheet/default.asp?caltimesheet=1,7')
        return self._parse_response(response)
    
    def next_month(self):
        response = self._browser.open('https://currenttime.bouvet.no/Timesheet/default.asp?caltimesheet=1,8')
        self._page = self._get_entire_month()
        return self.current_month()

    def previous_month(self):
        response = self._browser.open('https://currenttime.bouvet.no/Timesheet/default.asp?caltimesheet=1,5')
        self._page = self._get_entire_month()
        return self.current_month()
    
    def next_year(self):
        response = self._browser.open('https://currenttime.bouvet.no/Timesheet/default.asp?caltimesheet=1,4')
        self._page = self._get_entire_month()
        return self.current_month()
    
    def previous_year(self):
        response = self._browser.open('https://currenttime.bouvet.no/Timesheet/default.asp?caltimesheet=1,1')
        self._page = self._get_entire_month()
        return self.current_month()
    
    def _parse_response(self, response):
        document = html.parse(response)
        return document.getroot()
    
    def current_month(self):
        els = self._page.xpath("/html/body/table[3]/tr/td[2]/table[1]/tr/td[1]/table[1][@class='calendar']/tr/td[2][@class='top']/b")
        heading = els[0]
        parts = heading.get("title").split(" ")
        start = parts[1]
        _,m,y=[int(x.lstrip("0")) for x in start.split(".")]
        return datetime.date(y,m,1)

ct = CurrentTime()    
