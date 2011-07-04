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

from lxml import html
import calendar
import datetime


class Project(object):
    def __init__(self, names, values):
        # Use an internal dict so we're immutable
        self._dict = {
            "project": names[0],
            "task": names[1],
            "subtask": names[2],
            "activity": names[3],
            "projectid": int(values[0]),
            "taskid": int(values[1]),
            "subtaskid": int(values[2]),
            "activityid": int(values[3])
            }

    def __repr__(self):
        return self.name

    @property
    def full_name(self):
        parts = [
            "%(project)s",
            "%(task)s",
            "%(subtask)s"
        ]

        if self._dict.get("activity"):
            parts.append("%(activity)s")

        result = " - ".join(parts) % self._dict

        return result.encode("utf-8")

    @property
    def project_id(self):
        return self._dict.get("projectid")

    @property
    def name(self):
        result = "%(project)s - %(task)s" % self._dict
        return result.encode("utf-8")

    def __str__(self):
        parts = [
            "projectid=%(projectid)s",
            "taskid=%(taskid)s",
            "subtaskid=%(subtaskid)s",
            "activityid=%(activityid)s"
        ]

        return ",".join(parts) % self._dict


class CurrentTimeParser(object):
    def _parse_response(self, response):
        _, _, contents = response
        return html.fromstring(contents)

    def _get_session_id(self, response):
        root = self._parse_response(response)

        elements = root.cssselect("input[name='sessionid']")
        for el in elements:
            return el.value

    def parse_navigation(self, response):
        return self.current_month(response)

    def current_month(self, response):
        root = self._parse_response(response)

        el = root.cssselect("td[class=accept]")[0]
        parts = el.text_content().strip().split(" ")
        start = parts[1]
        _, m, y = [int(x.lstrip("0")) for x in start.split(".")]
        return datetime.date(y, m, 1)

    def parse_projects(self, response):
        root = self._parse_response(response)

        projects = []
        for tr in root.xpath("/html/body/table/tr/td[2]/form[2]/table[3]/tr"):
            if not tr.get("name"):
                continue

            values = []
            for el in tr.cssselect("input[type=hidden]"):
                values = el.value.split(",")
            if not values:
                continue

            names = [(x.text or '') for x in tr.cssselect("td[class=text]")]
            project = Project(names, values)
            projects.append(project)

        return dict([(str(p), p) for p in projects])

    def get_hours(self, response):
        result = []

        root = self._parse_response(response)
        month = self.current_month(response)

        rows = root.cssselect("input[name=activityrow]")[0].value
        for i in range(1, int(rows) + 1):
            projectel = root.cssselect("input[name=activityrow_%s]" % i)[0]
            project = ",".join(projectel.value.split(",")[:4])

            ro_hours = self._get_ro_hours(projectel, project, month, root, i)
            rw_hours = self._get_rw_hours(project, month, root, i)
            result.extend(ro_hours)
            result.extend(rw_hours)

        return result

    def _get_ro_hours(self, projectel, project, month, root, i):
        result = []

        row = projectel.getparent().getparent()
        row_root = root.getroottree().getpath(row)
        ro_classes = [
            "@class='datacol'",
            "@class='lastcol'",
            "@class='holiday'",
            "@class='readonly'"
        ]
        tds = root.xpath("%s/td[%s]" % (row_root, " or ".join(ro_classes)))

        for date in self._days_in_month(month):
            day = date.day
            hours = self._hours_to_float(tds[(day - 1) * 2][0].text)
            if not hours:
                continue

            comment = tds[(day - 1) * 2 + 1][0].text.strip()
            result.append((date, project, hours, comment))
        return result

    def _get_rw_hours(self, project, month, root, i):
        result = []
        for date in self._days_in_month(month):
            day = date.day
            cell = "cell_%s_%s" % (i, day)
            hours = root.cssselect("input[name=%s_duration]" % cell)
            if not hours:
                continue

            hours = self._hours_to_float(hours[0].value)
            comment = root.cssselect("input[name=%s_note]" % cell)[0].value
            result.append((date, project, hours, comment))
        return result

    def _days_in_month(self, date):
        _, num_days = calendar.monthrange(date.year, date.month)
        return [
            datetime.date(date.year, date.month, day)
            for day in range(1, num_days + 1)
        ]

    def _hours_to_float(self, hours_input):
        hours = hours_input.strip()
        if not hours:
            return 0.0

        return float(hours.replace(",", "."))
