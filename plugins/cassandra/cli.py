import sys
import logging
import urllib

from optparse import make_option

from cloud.plugin import CLIPlugin
from cloud.plugin import BASIC_OPTIONS
from cloud.service import InstanceTemplate
from cloud.util import log_cluster_action
from optparse import make_option
from prettytable import PrettyTable
from pprint import pprint

# Add options here to override what's in the clusters.cfg file
# TODO

class CassandraServiceCLI(CLIPlugin):
    USAGE = """Cassandra service usage: CLUSTER COMMAND [OPTIONS]
where COMMAND and [OPTIONS] may be one of:
            
                               CASSANDRA COMMANDS
  ----------------------------------------------------------------------------------
  start-cassandra                     starts the cassandra service on all nodes
  stop-cassandra                      stops the cassandra service on all nodes
  print-ring [INSTANCE_IDX]           displays the cluster's ring information
  rebalance                           recalculates tokens evenly and moves nodes
  remove-down-nodes                   removes nodes that are down from the ring

                               CLUSTER COMMANDS
  ----------------------------------------------------------------------------------
  details                             list instances in CLUSTER
  launch-cluster NUM_NODES            launch NUM_NODES Cassandra nodes
  expand-cluster NUM_NODES            adds new nodes
  terminate-cluster                   terminate all instances in CLUSTER
  login                               log in to the master in CLUSTER over SSH

                               STORAGE COMMANDS
  ----------------------------------------------------------------------------------
  list-storage                        list storage volumes for CLUSTER
  create-storage NUM_INSTANCES        create volumes for NUM_INSTANCES instances
    SPEC_FILE                           for CLUSTER, using SPEC_FILE
  delete-storage                      delete all storage volumes for CLUSTER
"""
    
    def __init__(self):
        super(CassandraServiceCLI, self).__init__()

        #self._logger = logging.getLogger("CassandraServiceCLI")
 
    def execute_command(self, argv, options_dict):
        if len(argv) < 2:
            self.print_help()

        self._cluster_name = argv[0]
        self._command_name = argv[1]

        # strip off the cluster name and command from argv
        argv = argv[2:]

        # handle all known commands and error on an unknown command
        if self._command_name == "details":
            self.print_instances()
            
        elif self._command_name == "simple-details":
            self.simple_print_instances(argv, options_dict)

        elif self._command_name == "terminate-cluster":
            self.terminate_cluster(argv, options_dict)

        elif self._command_name == "launch-cluster":
            self.launch_cluster(argv, options_dict)

        elif self._command_name == "expand-cluster":
            self.expand_cluster(argv, options_dict)

        elif self._command_name == "replace-down-nodes":
            self.replace_down_nodes(argv, options_dict)

        elif self._command_name == "login":
            self.login(argv, options_dict)

        elif self._command_name == "run-command":
            self.run_command(argv, options_dict)

        elif self._command_name == "transfer-files":
            self.transfer_files(argv, options_dict)

        elif self._command_name == "create-storage":
            self.create_storage(argv, options_dict)

        elif self._command_name == "delete-storage":
            self.delete_storage(argv, options_dict)

        elif self._command_name == "list-storage":
            self.print_storage()

        elif self._command_name == "stop-cassandra":
            self.stop_cassandra(argv, options_dict)

        elif self._command_name == "start-cassandra":
            self.start_cassandra(argv, options_dict)

        elif self._command_name == "print-ring":
            self.print_ring(argv, options_dict)

        elif self._command_name == "hack-config-for-multi-region":
            self.hack_config_for_multi_region(argv, options_dict)
            
        elif self._command_name == "rebalance":
            self.rebalance(argv, options_dict)

        elif self._command_name == "remove-down-nodes":
            self.remove_down_nodes(argv, options_dict)
        else:
            self.print_help()

    def expand_cluster(self, argv, options_dict):
        expected_arguments = ["NUM_INSTANCES"]
        opt, args = self.parse_options(self._command_name,
                                       argv,
                                       expected_arguments=expected_arguments,
                                       unbounded_args=True)
        opt.update(options_dict)

        number_of_nodes = int(args[0])
        instance_template = InstanceTemplate(
            (self.service.CASSANDRA_NODE,),
            number_of_nodes,
            opt.get('image_id'),
            opt.get('instance_type'),
            opt.get('key_name'),
            opt.get('public_key'),
            opt.get('user_data_file'),
            opt.get('availability_zone'),
            opt.get('user_packages'),
            opt.get('auto_shutdown'),
            opt.get('env'),
            opt.get('security_groups'))
#        instance_template.add_env_strings(["CLUSTER_SIZE=%d" % number_of_nodes])

        print "Expanding cluster by %d instance(s)...please wait." % number_of_nodes

        self.service.expand_cluster(instance_template)

    def replace_down_nodes(self, argv, options_dict):
        opt, args = self.parse_options(self._command_name,
                                       argv)
        opt.update(options_dict)

        # test files
        for key in ['cassandra_config_file']:
            if opt.get(key) is not None:
                try:
                    url = urllib.urlopen(opt.get(key))
                    data = url.read()
                except:
                    raise
                    print "The file defined by %s (%s) does not exist. Aborting." % (key, opt.get(key))
                    sys.exit(1)

        number_of_nodes = len(self.service.calc_down_nodes())
        instance_template = InstanceTemplate(
            (self.service.CASSANDRA_NODE,),
            number_of_nodes,
            opt.get('image_id'),
            opt.get('instance_type'),
            opt.get('key_name'),
            opt.get('public_key'),
            opt.get('user_data_file'),
            opt.get('availability_zone'),
            opt.get('user_packages'),
            opt.get('auto_shutdown'),
            opt.get('env'),
            opt.get('security_groups'))
#        instance_template.add_env_strings(["CLUSTER_SIZE=%d" % number_of_nodes])

        print "Replacing %d down instance(s)...please wait." % number_of_nodes

        self.service.replace_down_nodes(instance_template,
                                        opt.get('cassandra_config_file'))

    def launch_cluster(self, argv, options_dict):
        """
        """
        expected_arguments = ["NUM_INSTANCES"]
        opt, args = self.parse_options(self._command_name, 
                                      argv,
                                      expected_arguments=expected_arguments)
        opt.update(options_dict)

        if self.service.get_instances() :
            print "This cluster is already running.  It must be terminated prior to being launched again."
            sys.exit(1)

        number_of_nodes = int(args[0])
        instance_template = InstanceTemplate(
            (self.service.CASSANDRA_NODE,), 
            number_of_nodes,
            opt.get('image_id'),
            opt.get('instance_type'),
            opt.get('key_name'),
            opt.get('public_key'), 
            opt.get('user_data_file'),
            opt.get('availability_zone'), 
            opt.get('user_packages'),
            opt.get('auto_shutdown'), 
            opt.get('env'),
            opt.get('security_groups'))
        instance_template.add_env_strings(["CLUSTER_SIZE=%d" % number_of_nodes])

        print "Launching cluster with %d instance(s)...please wait." % number_of_nodes

        self.service.launch_cluster(instance_template, opt)


        log_cluster_action(opt.get('config_dir'), self._cluster_name,
            "launch-cluster", number_of_nodes, opt.get("instance_type"),
            None, "cassandra")

    def stop_cassandra(self, argv, options_dict):
        instances = self.service.get_instances()
        if not instances:
            print "No running instances. Aborting."
            sys.exit(1)

        print "Stopping Cassandra service on %d instance(s)...please wait." % len(instances)
        self.service.stop_cassandra(instances=instances)

    def start_cassandra(self, argv, options_dict):
        instances = self.service.get_instances()
        if not instances:
            print "No running instances. Aborting."
            sys.exit(1)

        print "Starting Cassandra service on %d instance(s)...please wait." % len(instances)
        self.service.start_cassandra(instances=instances)

    def print_ring(self, argv, options_dict):
        instances = self.service.get_instances()
        if not instances:
            print("No running instances. Aborting.")
            sys.exit(1)

        idx = 0
        if len(argv) > 0 :
            idx = int(argv[0])

        print(self.service.print_ring(instances[idx]))

    def hack_config_for_multi_region(self, argv, options_dict):
        instances = self.service.get_instances()
        if not instances:
            print "No running instances. Aborting."
            sys.exit(1)

        opt_list = BASIC_OPTIONS + [make_option("--seeds", metavar="SEEDS", action="store", type="str", default="",  help="explicit comma separated seed list")]
        opt, args = self.parse_options(self._command_name, argv, opt_list)

        self.service.hack_config_for_multi_region(options_dict.get('ssh_options'), opt['seeds'])
        
    def rebalance(self, argv, options_dict):
        instances = self.service.get_instances()
        if not instances:
            print "No running instances. Aborting."
            sys.exit(1)

        opt, args = self.parse_options(self._command_name, argv, [make_option("--offset", metavar="OFFSET", action="store", type=int, default=0, help="token offset")])
        self.service.rebalance(offset=opt['offset'])

    def remove_down_nodes(self, argv, options_dict):
        instances = self.service.get_instances()
        if not instances:
            print "No running instances. Aborting."
            sys.exit(1)

        self.service.remove_down_nodes()

    def create_storage(self, argv, options_dict):
        opt, args = self.parse_options(self._command_name, argv, BASIC_OPTIONS,
                                       ["NUM_INSTANCES", "SPEC_FILE"])
        opt.update(options_dict)

        role = self.service.CASSANDRA_NODE
        number_of_instances = int(args[0])
        spec_file = args[1]

        # FIXME
        # check_options_set(opt, ['availability_zone'])

        self.service.create_storage(role, 
                                    number_of_instances,
                                    opt.get('availability_zone'),
                                    spec_file)
        self.print_storage()
