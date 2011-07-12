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

import os
import sys
import argparse
import datetime
from collections import defaultdict
from ct.apis import SimpleAPI
import ConfigParser

config = ConfigParser.ConfigParser()
user_cfg = os.path.expanduser('~/.ct.cfg')
default_cfg = os.path.join(
    sys.prefix,
    'share/ct/config.ini.sample')

config.read([default_cfg, user_cfg])

server = config.get("server", "url")
username = config.get("login", "username")
password = config.get("login", "password")


now = datetime.datetime.now()

parser = argparse.ArgumentParser()
parser.add_argument('-m', dest='month', type=int, default=now.month,
   help='The month number to list hours from, defaults to current month')
parser.add_argument('-y', dest='year', type=int, default=now.year,
   help='The year to list hours from, defaults to current year')
args = parser.parse_args()

ct = SimpleAPI(server)
if ct.login(username, password):
    result = defaultdict(lambda: 0)
    for activity in ct.get_activities(args.year, args.month):
        result[activity.project_id] += activity.duration

    project_map = dict([(p.id, p) for p in ct.get_projects()])
    for project_id, worked in sorted(result.items()):
        if not worked:
            continue

        print "%04s: %s" % (worked, project_map[project_id].name)
else:
    print "Could not login."
