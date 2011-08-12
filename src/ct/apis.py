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
import unittest

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

        return self._browser.update(session_id, activity)

    def delete_activity(self, activity):
        session_id = self._parser.parse_session_id(self._browser.current_page)
        if not self._is_in_correct_state(activity.day):
            raise ValueError(
                "Date argument is not withing the currently displayed date.")

        return self._browser.delete(session_id, activity)

    def valid_session(self):
        return self._parser.valid_session(self._browser.current_page)

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

    def valid_session(self):
        return self._ct.valid_session()

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

    def delete_activity(self, activity):
        self._goto_year(activity.day.year)
        self._goto_month(activity.day.month)
        return self._ct.delete_activity(activity)



class RangeAPI(object):
    def __init__(self, server):
        self._ct = SimpleAPI(server)

    def login(self, username, password):
        return self._ct.login(username, password)

    def valid_session(self):
        return self._ct.valid_session()

    def get_projects(self, *args, **kwargs):
        return self._ct.get_projects(*args, **kwargs)

    def get_activities(self, from_date, to_date):
        activities = []
        for year, month in self._get_months_in_range(from_date, to_date):
            for activity in self._ct.get_activities(year, month):
                if from_date <= activity.day and activity.day <= to_date:
                    activities.append(activity)

        return activities

    def report_activity(self, activity, previous=None):
        self._perform_optimistic_concurrency_validation(activity, previous)
        return self._ct.report_activity(activity)

    def delete_activity(self, activity, previous=None):
        self._perform_optimistic_concurrency_validation(activity, previous)
        return self._ct.delete_activity(activity)

    def _get_months_in_range(self, from_date, to_date):
        year, month = from_date.year, from_date.month
        while (year, month) <= (to_date.year, to_date.month):
            yield year, month

            month += 1
            if month > 12:
                month = 1
                year += 1

    def _perform_optimistic_concurrency_validation(self, activity, previous):
        activities = self.get_activities(activity.day, activity.day)
        if not previous and activity in activities:
            index = activities.index(activity)
            previous = activities[index]
            raise ActivityAlreadyExists(activity, previous)

        if not previous in activities:
            raise PreviousActivityNotFound(activity, previous)

        index = activities.index(previous)
        actual_previous = activities[index]
        if self._has_changed(previous, actual_previous):
            raise PreviousActivityChanged(activity, actual_previous)

    def _has_changed(self, form_previous, actual_previous):
        return form_previous != actual_previous


class TestRangeAPI(unittest.TestCase):
    def test_1_month_in_same_month_and_year(self):
        api = RangeAPI("no-server")
        from_date = to_date = datetime.date(2011, 6, 1)
        months = list(api._get_months_in_range(from_date, to_date))

        self.assertEquals(1, len(months))

    def test_2_months_in_same_year_and_following_month(self):
        api = RangeAPI("no-server")
        from_date = datetime.date(2011, 6, 1)
        to_date = datetime.date(2011, 7, 1)
        months = list(api._get_months_in_range(from_date, to_date))

        self.assertEquals(2, len(months))

    def test_13_months_in_same_month_and_following_year(self):
        api = RangeAPI("no-server")
        from_date = datetime.date(2011, 6, 1)
        to_date = datetime.date(2012, 6, 1)
        months = list(api._get_months_in_range(from_date, to_date))

        self.assertEquals(13, len(months))


class ActivityConflict(Exception):
    def __init__(self, new_value, current_value):
        self.new_value = new_value
        self.current_value = current_value


class ActivityAlreadyExists(ActivityConflict):
    pass


class PreviousActivityChanged(ActivityConflict):
    pass


class PreviousActivityNotFound(ActivityConflict):
    pass

if __name__ == "__main__":
    unittest.main()
