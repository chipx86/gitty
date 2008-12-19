import os


class Diff(object):
    def __init__(self, commit_sha1, parent_sha1):
        self.commit_sha1 = None
        self.parent_sha1 = None



    def __unicode__(self):
        return self.contents
