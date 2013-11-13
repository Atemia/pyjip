#!/usr/bin/env python
"""JIP module that handles job profiles. A job profile
contains all compute-cluster related meta-data of a job, such as the number
of threads reserved for the job or the time limit. Profiles can be named and
stored in the user configuration. In addition, hierarical updated of
profiles can be applied. For example, a default profile can be loaded from
the configuration. This profile can than be refiend by a pipeline script
or command line options.
"""
import collections
import re
import os
import json

import jip.utils
from jip.templates import render_template

#: global specs
specs = None


class Profile(object):
    """A Profile contains cluster and runtime specific information about
    a job.
    """
    def __init__(self, name=None, threads=None,
                 time=None, queue=None, priority=None,
                 log=None, out=None, account=None, mem=0, extra=None,
                 profile=None, prefix=None, temp=False, _load=True, env=None,
                 tool_name=None, working_dir=None):
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
        self.env = None
        self.temp = temp
        self.extra = extra
        self.job_specs = None
        self.tool_name = tool_name
        self.working_dir = working_dir
        if profile is not None and _load:
            self.load(profile)

    def load(self, profile_name):
        """Set this profiles values to the values loaded from the profile
        stored under the given name. An exception is raised if no profile of
        that name could be found.

        :param profile_name: the name of the profile that will be loaded
        :type profile_name: string
        """
        import jip
        profiles = jip.config.get('profiles', {})
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
        self.extra = profile.get('extra', self.extra)
        self.enc = profile.get('env', self.env)

    def load_args(self, args):
        """Update this profile from the given dictionary of command line
        arguments. The argument names must match the profile attributes
        """
        for k, v in args.iteritems():
            k = re.sub("^-+", "", k)
            if v and hasattr(self, k):
                setattr(self, k, v)

    def apply(self, job, _load_specs=True, overwrite_threads=False):
        """Apply this profile to a given job and all its ambedded children
        All non-None values are applied to the given job.
        """
        r = render_template
        ctx = {}
        for o in job.tool.options:
            ctx[o.name] = o
        name = job.name
        if not name:
            name = self.name
        if not name:
            name = job._tool.name
        job.name = r("%s%s" % ("" if not self.prefix else self.prefix,
                               name), **ctx)
        if self.threads is not None and job.threads is None:
            if not overwrite_threads:
                job.threads = max(int(self.threads), job.threads)
            else:
                job.threads = int(self.threads)

        if self.queue is not None:
            job.queue = self.queue
        if self.priority is not None:
            job.priority = self.priority
        if self.time is not None:
            job.max_time = jip.utils.parse_time(self.time)
        if self.mem is not None:
            job.max_memory = self.mem
        if self.log is not None:
            job.err = self.log
        if self.out is not None:
            job.out = self.out
        if self.account is not None:
            job.account = self.account
        if self.temp is not None:
            job.temp = self.temp
        if self.extra is not None:
            job.extra = self.extra
        if self.working_dir is not None:
            job.working_directory = os.path.abspath(self.working_dir)

        # load environment
        if self.env:
            current = os.environ.copy()
            if job.env:
                current.update(job.env)
            rendered = {}
            for k, v in self.env.iteritems():
                rendered[k] = render_template(v, **current)
            job.env.update(rendered)

        if specs is None:
            get_specs()

        if _load_specs:
            if job.tool.name in specs:
                # apply the job spec
                spec_profile = Profile(threads=self.threads)
                spec_profile.load_spec(specs[job.tool.name], None)
                spec_profile.apply(job, False, overwrite_threads=True)

            if self.tool_name in specs:
                # apply the job spec
                spec_profile = Profile(threads=self.threads)
                spec_profile.load_spec(specs[self.tool_name], None)
                spec_profile.apply(job, False)
                spec = specs[self.tool_name]
                if 'jobs' in spec and job.tool.name in spec['jobs']:
                    spec_profile = Profile(threads=self.threads)
                    spec_profile.load_spec(spec['jobs'][job.tool.name], None)
                    spec_profile.apply(job, False, overwrite_threads=True)

        if self.job_specs is not None and job.tool.name in self.job_specs:
            # apply the job spec
            spec_profile = Profile(threads=self.threads)
            spec_profile.load_spec(self.job_specs[job.tool.name], None)
            spec_profile.apply(job, False, overwrite_threads=True)

        if hasattr(job, 'pipe_to'):
            for child in job.pipe_to:
                self.apply(child)

    def __call__(self, name=None, threads=None,
                 time=None, queue=None, priority=None,
                 log=None, out=None, account=None, mem=None,
                 profile=None, prefix=None, temp=False, extra=None,
                 dir=None):
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
            temp=temp if temp is not None else self.temp,
            extra=extra if extra is not None else self.extra,
            working_dir=dir if dir is not None else self.working_dir,
            _load=False
        )

    def __repr__(self):
        return str(vars(self))

    def load_spec(self, spec, tool):
        """Update this profile from the specifications default parameters

        :param spec: dictionary with the job specification
        :param tool: name of the tool or pipeline
        """
        if spec is not None and (tool is None or tool in spec):
            d = spec if tool is None or tool not in spec else spec[tool]
            for k, v in d.iteritems():
                if v is None:
                    continue
                self.__setattr__(k, v)
            if tool is not None and 'jobs' in spec[tool]:
                self.job_specs = spec[tool]['jobs']


def get(name='default', tool=None):
    """Load a profile by name. If tools is speciefied, the specs are
    searched to the tool and if found, the spec is applied.
    """
    p = Profile(profile=name)
    return p


def get_specs(path=None):
    """Load specs form default locations and then update from specs in given
    path if specified.

    :param path: optional path to an additional spec file
    """
    global specs
    cwd = os.path.join(os.getcwd(), "jip.specs")
    home = os.path.join(os.getenv("HOME", ""), ".jip/jip.specs")
    specs = {}
    if os.path.exists(home):
        with open(home) as of:
            specs = _update(specs, json.load(of))
    if os.path.exists(cwd):
        with open(cwd) as of:
            specs = _update(specs, json.load(of))
    if path and os.path.exists(path):
        with open(path) as of:
            specs = _update(specs, json.load(of))
    return specs


def _update(config, other):
    for k, v in other.iteritems():
        if isinstance(v, collections.Mapping):
            r = _update(config.get(k, {}), v)
            config[k] = r
        else:
            config[k] = other[k]
    return config
