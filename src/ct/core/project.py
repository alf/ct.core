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

    def __str__(self):
        return self.id

    def __repr__(self):
        return self.name.encode('utf-8')

    @property
    def name(self):
        parts = [
            "%(project)s",
            "%(task)s",
            "%(subtask)s"
        ]

        if self._dict.get("activity"):
            parts.append("%(activity)s")

        return " - ".join(parts) % self._dict

    @property
    def id(self):
        s = "%(projectid)s,%(taskid)s,%(subtaskid)s,%(activityid)s"
        return s % self._dict

    @property
    def project_name(self):
        return self._dict.get("project")

    @property
    def task_name(self):
        return self._dict.get("task")

    @property
    def subtask_name(self):
        return self._dict.get("subtask")

    @property
    def activity_name(self):
        return self._dict.get("activity")
