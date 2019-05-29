import os
from kazoo.client import KazooClient


# ZOOKEEPER

def read_bytes(zk, key):
    if not zk.exists(key):
        raise ValueError 

    data, stat = zk.get(key)
    if data:
        try:
            print("Version: %s, unicode data: %s" % (stat.version, data.decode("utf-8")))
        except UnicodeDecodeError:
            print("Version: %s, raw data: %s" % (stat.version, data))
    else:
        print("Version: %s, data: None" % (stat.version))

    return data

def write_bytes(zk, key, value):
    if zk.exists(key):
        raise ValueError 

    zk.ensure_path(os.path.dirname(key))
    return zk.create(key, value)


# BACKUP STORAGE

def write_to(fname):
    def write(value):
        with open(fname, 'wb') as f:
            f.write(value)
    return write

def read_from(fname):
    def read():
        with open(fname, 'rb') as f:
            value = f.read()
        return value
    return read

def get_backup_for(key):
    return "./{name}.dump".format(name=key.replace("/", "_"))

def create_write(key):
    backup = get_backup_for(key)
    return write_to(backup)

def create_read(key):
    backup = get_backup_for(key)
    return read_from(backup)


# TOOL

def create_backup_operation(zk):
    def backup_value(key):
        write = create_write(key)
        value = read_bytes(zk, key)
        if value:
            write(value)
        return value
    return backup_value

def create_restore_operation(zk):
    def restore_value(key):
        read = create_read(key)
        restored_value = read()
        write_bytes(zk, key, restored_value)
        return restored_value
    return restore_value

def run(keys, run_operation):
    values = []
    for key in keys:
        values.append(run_operation(key))
    return values


def main(options, zk, keys):
    if options['task'] == 'BACKUP':
        backup_op = create_backup_operation(zk)
        run(keys, backup_op)

    if options['task'] == 'RESTORE':
        restore_op = create_restore_operation(zk)
        run(keys, restore_op)


# INJECT

def load_scenario_zoo():
    keys = ["/archives/1", "/archives/2", "/archives/3"]
    zk = KazooClient(hosts='localhost:2181')
    return zk, keys

class Status(object):
    version = 0.1

class TestClient(object):
    def __init__(self, state):
        self.store = state
        self.stat = Status()
    def start(self):
        pass
    def stop(self):
        pass
    def get(self, key):
        return self.store[key], self.stat
    def exists(self, key):
        return (key in self.store)
    def ensure_path(self, path):
        pass
    def create(self, key, value):
        return value

def load_scenario_backup_test():
    keys = ["/archives/1", "/archives/2", "/archives/3"]
    state = {"/archives/1": "full", "/archives/2": "empty", "/archives/3": "empty"}
    zk = TestClient(state)
    return zk, keys

def load_scenario_restore_test():
    keys = ["/archives/1", "/archives/2", "/archives/3"]
    state = dict()
    zk = TestClient(state)
    return zk, keys


if __name__ == '__main__':
    options = {'task': 'RESTORE'}

    zk, keys = load_scenario_restore_test()
    zk.start()

    main(options, zk, keys)

    zk.stop()
