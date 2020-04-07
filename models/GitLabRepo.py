import subprocess
import gitlab


class GitLabRepo:
    def __init__(self, name=None, path=None, creator=None, mirror=None):
        self.name = name
        self.mirror = mirror
        self.creator = creator
        self.path = path

