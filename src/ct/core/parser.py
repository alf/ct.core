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
from decimal import Decimal

from ct.core.project import Project
from ct.core.activity import Activity


class CurrentTimeParser(object):
    def _parse_response(self, response):
        return html.fromstring(response)

    def parse_session_id(self, response):
        root = self._parse_response(response)

        elements = root.cssselect("input[name='sessionid']")
        for el in elements:
            return el.value

    def valid_session(self, response):
        root = self._parse_response(response)
        return len(root.cssselect("body[class=login]")) == 0

    def _parse_navigation(self, response):
        root = self._parse_response(response)
        script = root.cssselect("table table script")[0].text_content()
        parts = script.split("'")
        date = datetime.datetime.strptime(parts[1], "%Y%m").date()
        calname = parts[3]
        return {
            'date': date,
            'calname': calname,
        }

    def parse_navigation(self, response):
        return self._parse_navigation(response)['date']

    def get_day_command(self, response, day):
        root = self._parse_response(response)
        days = root.cssselect("td[class=date]")
        for el in days:
            if int(el.text_content()) == day:
                url = el[0][0].get("href")
                _, command = url.split("?")

                parts = el[0][0].get("onclick").split(",")
                row = parts[2]
                column = parts[3].split(")")[0]
                if command:
                    command += "&"
                command += "caltimesheet=%s,%s" % (row.strip(), column.strip())
                return command

    def get_week_command(self, response, week):
        root = self._parse_response(response)
        weeks = root.cssselect("td[class=week]")
        for el in weeks:
            if int(el.text_content()) == week:
                url = el[0][0].get("href")
                _, command = url.split("?")
                return command

    def _parse_date(self, s):
        return datetime.datetime.strptime(s,"%d.%m.%Y").date()

    def _get_current_range(self, response):
        root = self._parse_response(response)

        el = root.cssselect("td[class=accept]")[0]
        parts = el.text_content().strip().split(" ")
        if len(parts) > 3:
            start = parts[1]
            end = parts[3]
        else:
            start, end = parts[1], parts[1]
        return self._parse_date(start), self._parse_date(end)

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

        return projects

    def parse_activities(self, response):
        activities = []

        root = self._parse_response(response)
        start, end = self._get_current_range(response)

        rows = root.cssselect("input[name=activityrow]")[0].value
        for i in range(1, int(rows) + 1):
            row = self._parse_row(start, end, root, i)
            activities.extend(row)
        return sorted(activities)

    def _parse_row(self, start, end, root, i):
        result = []

        projectel = root.cssselect("input[name=activityrow_%s]" % i)[0]
        project_id = self._parse_project_id(projectel.value)
        salary_id = self._parse_salary_id(projectel.value)

        row = projectel.getparent().getparent()
        row_root = root.getroottree().getpath(row)
        ro_classes = [
            "@class='datacol'",
            "@class='lastcol'",
            "@class='holiday'",
            "@class='readonly'"
        ]
        tds = root.xpath("%s/td[%s]" % (row_root, " or ".join(ro_classes)))

        for n, date in enumerate(self._dates(start, end)):
            i = n * 2
            duration_cell = tds[i][0]
            comment_cell = tds[i+1][0]
            if duration_cell.tag == "div" and len(duration_cell) > 0:
                duration, comment = self._parse_div(duration_cell, comment_cell)
                read_only = False
            else:
                duration, comment = self._parse_text(duration_cell, comment_cell)
                read_only = True

            activity = Activity(
                date,
                project_id,
                duration,
                comment,
                read_only=read_only,
                salary_id=salary_id)
            result.append(activity)
        return result

    def _parse_div(self, duration_cell, comment_cell):
        hours = self._parse_hours(duration_cell[0].value)
        comment = comment_cell[0].value.strip()
        return hours, comment

    def _parse_text(self, duration_cell, comment_cell):
        hours = self._parse_hours(duration_cell.text)
        comment = comment_cell.text.strip()
        return hours, comment

    def _dates(self, start, end):
        current = start
        while current <= end:
            yield current
            current += datetime.timedelta(days=1)

    def _parse_hours(self, value):
        hours = value.strip().replace(",", ".")
        return Decimal(hours or 0)

    def _parse_project_id(self, value):
        parts = value.strip().split(",")[:4]
        ids = [x.split("=")[1] for x in parts]
        return ",".join(ids)

    def _parse_salary_id(self, value):
        parts = value.strip().split(",")[4:]
        return ",".join(parts)
