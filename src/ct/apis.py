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
    def __init__(self):
        self._browser = CurrentTimeBrowser()
        self._parser = CurrentTimeParser()

    @property
    def current_date(self):
        return self._parser.current_month(self._browser.current_page)

    def report_activity(self, project, date, hours, comment):
        session_id = self._parser.get_session_id(self._browser.current_page)
        if not self._is_in_correct_state(date):
            raise ValueError(
                "Date argument is not withing the currently displayed date.")

        response = self._browser.post(
            session_id, project, date.day, hours, comment)
        return self._parser._parse_post_response(response)

    def list_activities(self):
        return self._parser.get_hours(self._browser.current_page)

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
        current = self._parser.get_current_month(self._browser.current_page)
        return current.year == date.year and current.month == date.month


class SimpleAPI(object):
    def __init__(self):
        self._ct = BaseAPI()

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

    def list_activities(self, year, month):
        self._goto_year(year)
        self._goto_month(month)

        projects = self.get_projects()
        activities = []
        for day, project, hours, comment in self._ct.list_activities():
            activity = {
                'day': day,
                'hours': hours,
                'comment': comment,
                'project': projects[project],
            }
            activities.append(activity)
        return activities

    def report_activity(self, project, date, hours, comment):
        self._goto_year(date.year)
        self._goto_month(date.month)
        return self._ct.report_activity(project, date, hours, comment)

    def get_projects(self, *args, **kwargs):
        return self._ct.get_projects(*args, **kwargs)
