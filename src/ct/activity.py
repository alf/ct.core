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

from decimal import Decimal

class Activity(object):
    def __init__(self, day, project_id, duration, comment, read_only=False):
        # Use an internal dict so we're immutable
        self._dict = {
            'day': day,
            'project_id': project_id,
            'duration': Decimal(str(duration)),
            'comment': comment,
            'read_only': read_only,
        }

    def __cmp__(self, other):
        return cmp(
            (self.day, self.project_id),
            (other.day, other.project_id))

    def __eq__(self, other):
        return self._dict == other._dict

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.day, self.project_id))

    def __str__(self):
        return str(self._dict)

    def has_activity(self):
        return self._dict["duration"] != 0.0

    @property
    def day(self):
        return self._dict['day']

    @property
    def project_id(self):
        return self._dict['project_id']

    @property
    def duration(self):
        return self._dict['duration']

    @property
    def comment(self):
        return self._dict['comment']

    @property
    def is_read_only(self):
        return self._dict['read_only']

