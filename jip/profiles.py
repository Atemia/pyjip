#!/usr/bin/env python
"""JIP module that handles job profiles. A job profile
contains all compute-cluster related meta-data of a job, such as the number
of threads reserved for the job or the time limit. Profiles can be named and
stored in the user configuration. In addition, hierarical updated of
profiles can be applied. For example, a default profile can be loaded from
the configuration. This profile can than be refiend by a pipeline script
or command line options.
"""
from jip.templates import render_template


class Profile(object):
    """A Profile contains cluster and runtime specific information about
    a job.
    """

    """Container class that wrapps job meta-data"""
    def __init__(self, name=None, threads=None,
                 time=None, queue=None, priority=None,
                 log=None, out=None, account=None, mem=None,
                 profile=None, prefix=None, _load=True):
        if profile is not None and _load:
            self.load(profile)
        self.name = render_template(name)
        self.threads = render_template(threads)
        self.profile = render_template(profile)
        self.queue = render_template(queue)
        self.time = render_template(time)
        self.mem = render_template(mem)
        self.priority = render_template(priority)
        self.log = render_template(log)
        self.out = render_template(out)
        self.account = render_template(account)
        self.prefix = render_template(prefix)

    def load(self, profile_name):
        """Set this profiles values to the values loaded from the profile
        stored under the given name. An exception is raised if no profile of
        that name could be found.

        :param profile_name: the name of the profile that will be loaded
        :type profile_name: string
        """
        import jip
        profiles = jip.configuration.get('profiles', {})
        if profile_name not in profiles:
            raise ValueError("Profile %s not found!" % profile_name)
        profile = profiles[profile_name]

        self.threads = profile.get('threads', self.threads)
        self.time = profile.get('time', self.time)
        self.queue = profile.get('queue', self.queue)
        self.priority = profile.get('priority', self.priority)
        self.log = profile.get('log', self.log)
        self.out = profile.get('out', self.out)
        self.account = profile.get('account', self.account)
        self.mem = profile.get('mem', self.mem)

    def apply(self, job):
        """Apply this profile to a given job.
        All non-None values are applied to the given job.
        """
        if self.name is not None:
            job.name = "%s%s" % ("" if not self.prefix else self.prefix,
                                 self.name)
        if self.threads is not None:
            job.threads = int(self.threads)
        if self.queue is not None:
            job.queue = self.queue
        if self.priority is not None:
            job.priority = self.priority
        if self.time is not None:
            job.time = self.time
        if self.mem is not None:
            job.mem = self.mem
        if self.log is not None:
            job.err = self.log
        if self.out is not None:
            job.out = self.out
        if self.account is not None:
            job.account = self.account

    def __call__(self, name=None, threads=None,
                 time=None, queue=None, priority=None,
                 log=None, out=None, account=None, mem=None,
                 profile=None, prefix=None):
        return self.__class__(
            name=name if name is not None else self.name,
            threads=threads if threads is not None else self.threads,
            profile=profile if profile is not None else self.profile,
            queue=queue if queue is not None else self.queue,
            time=time if time is not None else self.time,
            priority=priority if priority is not None else self.priority,
            log=log if log is not None else self.log,
            out=out if out is not None else self.out,
            account=account if account is not None else self.account,
            mem=mem if mem is not None else self.mem,
            prefix=prefix if prefix is not None else self.prefix,
            _load=False
        )