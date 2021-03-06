"""
The command line interface requires some persistent global state to operate
effectively. It stores this state in a JSON file in a hidden directory in the
user's home folder. The following is a record of all of the keys in that JSON
file and what they mean.

config["cloud_server"] - Holds information about the cloud CouchDB instance
selected by the current user

config["cloud_server"]["url"] - The URL of the cloud server (e.g.
"http://openag.mit.edu:5984")

config["cloud_server"]["username"] and
config["cloud_server"]["password"] - The credentials with which to log in to
the cloud server

config["cloud_server"]["farm_name"] - The name of the farm on the cloud server
into which to mirror data

config["local_server"] - Holds information about the local CouchDB instance
selected by the current user

config["local_server"]["url"] - The URL of the local server
"""
import os
import json
import errno
from click import get_app_dir

CONFIG_FOLDER = get_app_dir("openag", force_posix=True)
CONFIG_FILE = os.path.join(CONFIG_FOLDER, "config.json")

class PersistentObj(object):
    def __init__(self, data, parent):
        self._data = data
        self._parent = parent

    def __getitem__(self, attr):
        val = self._data.get(attr, dict())
        self._data[attr] = val
        if isinstance(val, dict):
            return PersistentObj(val, self)
        else:
            return val

    def __setitem__(self, attr, value):
        self._data[attr] = value
        self._save()

    def __delitem__(self, attr):
        del self._data[attr]
        self._save()

    def __nonzero__(self):
        return bool(self._data)

    def __iter__(self):
        self._clean()
        for key in self._data:
            yield key

    def items(self):
        self._clean()
        for k in self:
            yield k, self[k]

    def _clean(self):
        for k,v in self._data.items():
            if not v:
                del self._data[k]

    def _save(self):
        self._clean()
        self._parent._save()

class Config(PersistentObj):
    def __init__(self, filename=CONFIG_FILE):
        self.filename = filename
        folder = os.path.dirname(filename)
        try:
            os.makedirs(folder)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(folder):
                pass
            else:
                raise
        try:
            with open(filename) as f:
                self._data = json.load(f)
        except (IOError, ValueError):
            self._data = {}

    def _save(self):
        self._clean()
        with open(self.filename, "w+") as f:
            json.dump(self._data, f)

config = Config()
