# -*- coding: utf-8 -*-
# Copyright 2011 Alf Lervåg. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials
#       provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY ALF LERVÅG ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL ALF LERVÅG OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and
# documentation are those of the authors and should not be interpreted
# as representing official policies, either expressed or implied, of
# Alf Lervåg.

import datetime
import urllib
import urllib2
import cookielib
import ConfigParser

__all__ = ["CurrentTimeBrowser"]

def updates_current_page(meth):
    def decorate(self, *args, **kwargs):
        response = meth(self, *args, **kwargs)
        self._current_page = response
        return response
    return decorate


def invalidates_current_page(meth):
    def decorate(self, *args, **kwargs):
        self._current_page = None
        return meth(self, *args, **kwargs)
    return decorate


class CurrentTimeBrowser(object):
    URLS = {
        'login': 'login.asp',
        'get_current_month': 'Timesheet/default.asp?caltimesheet=1,7',
        'goto_next_month': 'Timesheet/default.asp?caltimesheet=1,8',
        'goto_prev_month': 'Timesheet/default.asp?caltimesheet=1,5',
        'goto_next_year': 'Timesheet/default.asp?caltimesheet=1,4',
        'goto_prev_year': 'Timesheet/default.asp?caltimesheet=1,1',
        'get_projects': 'Timesheet/projects.asp',
        'post_hours': 'Timesheet/default.asp',
    }

    def __init__(self):
        config = ConfigParser.ConfigParser()
        config.read(['config.ini.sample', 'config.ini'])

        self._server = config.get("server", "url")
        self._username = config.get("login", "username")
        self._password = config.get("login", "password")

        self.login()

    @property
    def current_page(self):
        if not getattr(self, '_current_page', None):
            self._current_page = self.get_current_month()

        return self._current_page

    def login(self):
        url = self._get_url('login')
        data = self._get_login_data()
        return self._open(url, data)

    @updates_current_page
    def get_current_month(self):
        url = self._get_url('get_current_month')
        return self._open(url)

    @invalidates_current_page
    def goto_next_month(self):
        url = self._get_url('goto_next_month')
        return self._open(url)

    @invalidates_current_page
    def goto_prev_month(self):
        url = self._get_url('goto_prev_month')
        return self._open(url)

    @invalidates_current_page
    def goto_next_year(self):
        url = self._get_url('goto_next_year')
        return self._open(url)

    @invalidates_current_page
    def goto_prev_year(self):
        url = self._get_url('goto_prev_year')
        return self._open(url)

    def get_projects(self, date=None):
        if date is None:
            date = datetime.datetime.now()

        datestr = date.strftime("%d.%m.%Y")

        data = urllib.urlencode({
                "fromdate": datestr,
                "todate": datestr,
                "search": "true",
        })

        url = self._get_url('get_projects')
        return self._open(url, data)

    @updates_current_page
    def post(self, session_id, project, day, hours, comment):
        url = self._get_url('post_hours')
        data = urllib.urlencode({
            "activityrow": "1",
            "activityrow_1": str(project),
            "cell_1_%s_duration" % day: hours,
            "cell_1_%s_note" % day: comment,
            "useraction": "save",
            "sessionid": session_id,
        })

        return self._open(url, data)

    def _open(self, *args):
        response = self._opener.open(*args)
        code = response.code
        headers = response.headers
        contents = response.read()
        return code, headers, contents

    @property
    def _opener(self):
        if not hasattr(self, '_my_opener'):
            self._my_opener = self._create_cookie_opener()
        return self._my_opener

    def _create_cookie_opener(self):
        cj = cookielib.CookieJar()
        return urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    def _get_url(self, name):
        rest = self.URLS.get(name)
        return "%s/%s" % (self._server, rest)

    def _get_login_data(self):
        return urllib.urlencode({
                'ctusername': self._username,
                'ctpassword': self._password,
                'browserversion': "ns6",
                'activex': "False",
                'useraction': "login",
                })
