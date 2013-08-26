import time
from ssh_helper import run_cmd, scp_to, scp_from
from chef import Node, Client
from subprocess import check_call, CalledProcessError


class OSNode:
    def __init__(self, ip, user, password,
                 config_manager=None, provisioner=None):
        self.ip = ip
        self.user = user
        self.password = password
        self.provisioner
        self.config_manager

    def run_cmd(self, remote_cmd, user=None, password=None, quiet=False):
        run_cmd(self.ip, remote_cmd=remote_cmd, user=user, password=password,
                quiet=quiet)

    def scp_to(self, local_path, remote_path=""):
        scp_to(self.ip, local_path, user=user, password=password, remote_path)

    def scp_from(self, remote_path, local_path=""):
        """
        @param path_to_file: file to copy
        @param copy_location: place on localhost to place file
        """

        command = ("sshpass -p %s scp "
                   "-o Self.UserKnownHostsFile=/dev/null "
                   "-o StrictHostKeyChecking=no "
                   "-o LogLevel=quiet "
                   "%s@%s:%s %s") % (self.password,
                                     self.user,
                                     self.ip,
                                     remote_path,
                                     local_path)

        try:
            ret = check_call(command, shell=True)
            return {'success': True,
                    'return': ret,
                    'exception': None}
        except CalledProcessError, cpe:
            return {'success': False,
                    'return': None,
                    'exception': cpe,
                    'command': command}

    def __str__(self):
        return "Node: %s" % self.ip

    def teardown(self):
        raise NotImplementedError


class OSDeployment:
    def __init__(self, name):
        self.name
        self.nodes = []

    def teardown(self):
        for node in self.nodes:
            node.teardown()


class ChefRazorOSDeployment:
    def __init__(self, chef, razor):
        self.chef = chef
        self.razor = razor

    def create_node(self):
        node = next(self.chef)
        config_manager = ChefConfigManager(node.name, self.chef)
        am_id = node.attributes['razor_metadata']['razor_active_model_uuid']
        provisioner = RazorProvisioner(self.razor, am_id)
        osnode = OSNode(ip, user, password, config_manager, provisioner)
        self.nodes.append(osnode)
        return osnode


class Provisioner():
    def teardown(self):
        raise NotImplementedError


class ConfigManager():
    def teardown(self):
        raise NotImplementedError


class ChefConfigManager(ConfigManager):
    def __init__(self, name, chef):
        self.name = name
        self.chef = chef

    def __str__(self):
        return "Chef Node: %s - %s" % (self.name, self.ip)

    def teardown(self):
        node = Node(self.name, self.api)
        Client(self.name).delete()
        node.delete()


class RazorProvisioner(Provisioner):
    def __init__(self, razor, id):
        self.razor = razor
        self._id = id

    def teardown(self):
        self.client.remove_active_model(self._id)
        run = self.run_cmd("reboot 0")
        if not run['success']:
            raise Exception("Error rebooting: " % self.__str__)
        time.sleep(15)