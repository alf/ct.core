#!/usr/bin/env python

from lxml import html
import calendar
import datetime
import urllib
import urllib2
import cookielib
import ConfigParser
from collections import defaultdict

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
        name = "%(project)s - %(task)s - %(subtask)s"
        if self._dict.get("activity"):
            name += " - %(activity)s"
        result = name % self._dict 
            
        return result.encode("utf-8")

    @property
    def name(self):
        result = "%(project)s - %(task)s" % self._dict
        return result.encode("utf-8")

    def __str__(self):
        return "projectid=%(projectid)s,taskid=%(taskid)s,subtaskid=%(subtaskid)s,activityid=%(activityid)s" % self._dict

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

    def goto_year(self, year):
        now = datetime.datetime.now()
        assert abs(now.year - year) < 25, "Year offset too large"

        current = self.current_month().year
        offset = abs(current - year)

        if current < year:
            for _ in range(offset):
                self.next_year()
        else:
            for _ in range(offset):
                self.previous_year()

    def goto_month(self, month):
        assert month > 0 and month <= 12

        current = self.current_month().month
        offset = abs(current - month)

        if current < month:
            for _ in range(offset):
                self.next_month()
        else:
            for _ in range(offset):
                self.previous_month()

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
    
    def _get_session_id(self):
        elements = self._page.cssselect("input[name='sessionid']") 
        for el in elements:
            return el.value

    def current_month(self):
        els = self._page.xpath("/html/body/table[3]/tr/td[2]/table[1]/tr/td[1]/table[1][@class='calendar']/tr/td[2][@class='top']/b")
        heading = els[0]
        parts = heading.get("title").split(" ")
        start = parts[1]
        _,m,y=[int(x.lstrip("0")) for x in start.split(".")]
        return datetime.date(y,m,1)

    def get_projects(self):
        date = self.current_month().strftime("%d.%m.%Y")
        data = urllib.urlencode({
                "fromdate": date,
                "todate": date,
                "search": "true",
        })
        response = self._browser.open("https://currenttime.bouvet.no/Timesheet/projects.asp", data)
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

    def get_hours(self, project_map={}):
        result = []
        rows = self._page.cssselect("input[name=activityrow]")[0].value
        for i in range(1, int(rows) + 1):
            projectel = self._page.cssselect("input[name=activityrow_%s]" % i)[0]
            project = ",".join(projectel.value.split(",")[:4])
            project = project_map.get(project, project)

            row = projectel.getparent().getparent()
            root = self._page.getroottree().getpath(row)
            tds = self._page.xpath(root + "/td[@class='datacol' or @class='lastcol' or @class='holiday' or @class='readonly']")

            for date in self.days_in_current_month():
                day = date.day
                cell = "cell_%s_%s" % (i, day)
                hours = self._page.cssselect("input[name=%s_duration]" % cell)
                if hours:
                    hours = self._hours_to_float(hours[0].value)
                    comment = self._page.cssselect("input[name=%s_note]" % cell)[0].value
                else:
                    hours = self._hours_to_float(tds[(day - 1) * 2][0].text)
                    comment = tds[(day - 1) * 2 + 1][0].text.strip()
                if hours:
                    result.append((date, project, hours, comment))
        return result

    def days_in_current_month(self):
        date = self.current_month()
        _, num_days = calendar.monthrange(date.year, date.month)
        return [datetime.date(date.year, date.month, day) for day in range(1, num_days + 1)]

    def post(self, project, day, hours, comment):
        data = urllib.urlencode({
            "activityrow": "1",
            "activityrow_1": str(project),
            "cell_1_%s_duration" % day: hours,
            "cell_1_%s_note" % day: comment,
            "useraction": "save",
            "sessionid": self._get_session_id(),
        })

        response = self._browser.open("https://currenttime.bouvet.no/Timesheet/default.asp", data)
        return self._parse_response(response)

    def _hours_to_float(self, hours_input):
        hours = hours_input.strip()
        if not hours:
            return 0.0

        return float(hours.replace(",", "."))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', dest='month', type=int, default=0,
                        help='The month number to list hours from, defaults to current month')
    parser.add_argument('-y', dest='year', type=int, default=0,
                        help='The year to list hours from, defaults to current year')
    args = parser.parse_args()

    ct = CurrentTime()

    if args.month > 0:
        ct.goto_month(args.month)

    if args.year > 0:
        ct.goto_year(args.year)

    result = defaultdict(lambda: 0)
    for date, project, hours, comment in ct.get_hours():
        result[project] += hours

    projects = ct.get_projects()
    for project, worked in result.items():
        print "%04s: %s" % (worked, projects[project].full_name)
        
        
        

