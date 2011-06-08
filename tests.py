#!/usr/bin/env python
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

import unittest

import datetime
from browser import CurrentTimeBrowser
from parser import CurrentTimeParser


class CurrentTimeParserTestCase(unittest.TestCase):
    def setUp(self):
        self.browser = CurrentTimeBrowser()
        self.parser = CurrentTimeParser()

    def test_that_we_get_current_month_on_login(self):
        current_date = self.parser.current_month(self.browser.current_page)

        now = datetime.datetime.now()
        expected_date = datetime.date(now.year, now.month, 1)

        self.assertEquals(expected_date, current_date)

    def test_that_current_date_is_previous_month_after_navigation(self):
        self.browser.goto_prev_month()

        current_date = self.parser.current_month(self.browser.current_page)

        now = datetime.datetime.now()
        expected_year = now.year
        expected_month = now.month - 1
        if expected_month < 1:
            expected_month = 12
            expected_year = expected_year - 1
        expected_date = datetime.date(expected_year, expected_month, 1)

        self.assertEquals(expected_date, current_date)

    def test_that_current_date_is_previous_year_after_navigation(self):
        self.browser.goto_prev_year()

        current_date = self.parser.current_month(self.browser.current_page)

        now = datetime.datetime.now()
        expected_date = datetime.date(now.year - 1, now.month, 1)

        self.assertEquals(expected_date, current_date)

if __name__ == '__main__':
    unittest.main()
