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
from parser import CurrentTimeParser
from browser import CurrentTimeBrowser

__all__ = ["BaseAPI", "SimpleAPI"]


class BaseAPI(object):
    def __init__(self, server):
        self._browser = CurrentTimeBrowser(server)
        self._parser = CurrentTimeParser()

    def login(self, username, password):
        return self._browser.login(username, password)

    @property
    def current_date(self):
        return self._parser.parse_current_month(self._browser.current_page)

    def report_activity(self, activity):
        session_id = self._parser.parse_session_id(self._browser.current_page)
        if not self._is_in_correct_state(activity.day):
            raise ValueError(
                "Date argument is not withing the currently displayed date.")

        response = self._browser.post(
            session_id,
            activity.project_id,
            activity.day.day,
            activity.duration,
            activity.comment)

        return response

    def get_activities(self):
        return self._parser.parse_activities(self._browser.current_page)

    def goto_next_month(self):
        response = self._browser.goto_next_month()
        return self._parser.parse_navigation(response)

    def goto_prev_month(self):
        response = self._browser.goto_prev_month()
        return self._parser.parse_navigation(response)

    def goto_next_year(self):
        response = self._browser.goto_next_year()
        return self._parser.parse_navigation(response)

    def goto_prev_year(self):
        response = self._browser.goto_prev_year()
        return self._parser.parse_navigation(response)

    def get_projects(self):
        response = self._browser.get_projects()
        return self._parser.parse_projects(response)

    def _is_in_correct_state(self, date):
        current = self._parser.parse_current_month(self._browser.current_page)
        return current.year == date.year and current.month == date.month


class SimpleAPI(object):
    def __init__(self, server):
        self._ct = BaseAPI(server)

    def login(self, username, password):
        return self._ct.login(username, password)

    def _goto_year(self, year):
        now = datetime.datetime.now()
        assert abs(now.year - year) < 25, "Year offset too large"

        current = self._ct.current_date.year
        offset = abs(current - year)

        if current < year:
            for _ in range(offset):
                self._ct.goto_next_year()
        else:
            for _ in range(offset):
                self._ct.goto_prev_year()

    def _goto_month(self, month):
        assert month > 0 and month <= 12

        current = self._ct.current_date.month
        offset = abs(current - month)

        if current < month:
            for _ in range(offset):
                self._ct.goto_next_month()
        else:
            for _ in range(offset):
                self._ct.goto_prev_month()

    def get_projects(self, *args, **kwargs):
        return self._ct.get_projects(*args, **kwargs)

    def get_activities(self, year, month):
        self._goto_year(year)
        self._goto_month(month)

        return self._ct.get_activities()

    def report_activity(self, activity):
        self._goto_year(activity.day.year)
        self._goto_month(activity.day.month)
        return self._ct.report_activity(activity)


class RangeAPI(object):
    def __init__(self, server):
        self._ct = SimpleAPI(server)

    def login(self, username, password):
        self._ct.login(username, password)

    def get_projects(self, *args, **kwargs):
        return self._ct.get_projects(*args, **kwargs)

    def get_activities(self, from_date, to_date):
        raise NotImplemented("Work in progress")

    def report_activity(self, activity, previous=None):
        raise NotImplemented("Work in progress")
