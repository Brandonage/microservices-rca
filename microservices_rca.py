from execo import SshProcess, Remote
import anomaly_injector_factory
import workflow_injector_factory
from random import shuffle
import time
import json
current_milli_time = lambda: int(round(time.time() * 1000))

"""
This is the main class that is going to start and inject the failures on the DCOS cluster
"""


class MicroServicesRCA():
    def __init__(self, masters, private_agents, public_agents, connection_params, orchestrator, experiment_log):
        # I dont know if we really need the master IP when we have the leader.mesos name to locate it
        # All and all there are three options: give to it one master, several masters, or None and just use
        # the leader.mesos name resolution with any of the slaves. I suppose this DNS also applies to K8
        """
        :param masters: a list for the masters or endpoints that ingest the container workflows
        :param private_agents: a list of the nodes that host the containers
        :param public_agents: a list of public access nodes. Normally they will hold load balancers and similar
        :param connection_params: a connection params dictionary for execo to connect to
        :param orchestrator: the type of orchestrator we are going to use
        :param experiment_log: a DF that has a log for all of the container workflows launched and anomalies injected
        """
        self.masters = masters
        # We choose to differentiate between private_agents and public_agents because they can have different purposes
        self.private_agents = private_agents
        self.public_agents = public_agents
        # We need all the slaves in order to do things like inject delay between two random nodes
        self.nodes = masters.union(public_agents.union(private_agents))
        # This is going to be the anomaly injector. Is going to have as a parameter some connection parameters for execo
        # We are going to have only one, but we could have more than one if we wanted to inject failures at different
        # levels. e.g. an anomaly injector at physical level, another at VM level, another on some other cluster with different
        # credentials and so on... for the sake of simplicity only one here
        # we also pass as a parameter the nodes of the cluster since we need to install some software on them to
        # generate these anomalies. HOWEVER we are only using them for the anomaly injector at the moment
        self.anomaly_injector = anomaly_injector_factory.get_anomaly_injector(orchestrator,
                                                                              self.nodes,
                                                                              connection_params)
        # same as the anomaly injector. But this one is going to inject workflows
        self.workflow_injector = workflow_injector_factory.get_workflow_injector(orchestrator,
                                                                                 self.nodes,
                                                                                 connection_params)
        # we are going to write into this log every operation done by the testbed in order to do a post analysis of the experiment
        self.experiment_log = experiment_log
        # we also keep the connection params on the MicroServicesRCA in case we need it to query API's from the testbed
        self.connection_params = connection_params

    def write_to_experiment_log(self, index, type, event, nodes, start, end, info):
        self.experiment_log.loc[index] = {
            "type": type,
            "event": event,
            "nodes": nodes,
            "date_start": start,
            "date_end": end,
            "aditional_info": info,
            "read_date": time.strftime("%c")
        }

    def list_all_running_containers(self):
        p = Remote('sudo docker ps',
                   hosts=self.nodes,
                   connection_params=self.connection_params).run()
        for process in p.processes:
            print("In the host {0} the following containers are alive: \n{1}".format(process.host, process.stdout))


    # From here we are going to include the scenarios that inject both workloads and anomalies. We decided to keep
    # this logic here in the MicroServicesRCA object instead of calling directly the injectors functions.
    # (e.g. microservices_rca.anomaly_injector.kill_node('192.167.143.12') The reason is that we might need to use both
    # injectors to create some scenarios. We also have the option of using the injectors but we will try to
    # keep as much logic here as possible

    def kafka_producer_consumer_scenario(self, nbrokers, nconsumers, nproducers):
        self.write_to_experiment_log(current_milli_time(), "workflow", "kafka_producer_consumer", "Scheduled by DCOS",
                                     int(time.time()),
                                     "unknown",
                                     "Brokers: {0} Producers: {1} Consumers: {2}".format(nbrokers, nproducers, nconsumers))
        curl_node = list(self.masters)[0]
        self.workflow_injector.kafka_producers_and_consumers(curl_node, nbrokers, nconsumers, nproducers)

    def lb_wordpress_scenario(self, nwordpress):
        self.write_to_experiment_log(current_milli_time(), "workflow", "lb_wordpress", "Scheduled by DCOS",
                                     int(time.time()),
                                     "unknown",
                                     "NWordpress: {0}".format(nwordpress))
        curl_node = list(self.masters)[0]
        vhost = list(self.private_agents)[0]
        self.workflow_injector.lb_wordpress(curl_node, nwordpress, vhost)

    def siege_http_clients_scenario(self, endpoint, ninstances, nclients, ntime, time_unit, delay):
        unit_in_seconds = {"S": 1, "M": 60, "H": 3600}
        self.write_to_experiment_log(current_milli_time(), "workflow", "siege_http_clients", "Scheduled by DCOS",
                                     int(time.time()),
                                     int(time.time()) + (int(ntime) * unit_in_seconds[time_unit]),
                                     "EndPoint: {0} Instances: {1} Clients: {2} Hours: {3} Delay: {4}".format(endpoint, ninstances, nclients, str(ntime) + time_unit, delay))
        curl_node = list(self.masters)[0]
        self.workflow_injector.siege_http_clients(curl_node,endpoint,ninstances,nclients,str(ntime) + time_unit,delay)

    def ab_clients_scenario(self,endpoint, ninstances, nclients, nrequests):
        self.write_to_experiment_log(current_milli_time(), "workflow", "ab_clients", "Scheduled by DCOS",
                                     int(time.time()), "record_time_manually",
                                     "EndPoint: {0} Instances: {1} Clients: {2} Requests: {3}".format(endpoint,
                                                                                                    ninstances,
                                                                                                    nclients,
                                                                                                    nrequests))
        curl_node = list(self.masters)[0]
        self.workflow_injector.ab_clients(curl_node,endpoint,ninstances,nclients,nrequests)

    def hadoop_cluster_scenario(self,ndatanodes,nnodemanagers):
        self.write_to_experiment_log(current_milli_time(), "workflow", "hadoop_cluster", "Scheduled by DCOS",
                                     int(time.time()),
                                     "unknown",
                                     "NDatanodes: {0} NNodemanagers: {1}".format(ndatanodes,nnodemanagers))
        curl_node = list(self.masters)[0]
        self.workflow_injector.hadoop_cluster(curl_node,ndatanodes,nnodemanagers)

    def spark_standalone_scenario(self,ndatanodes,nslaves):
        self.write_to_experiment_log(current_milli_time(), "workflow", "spark_standalone", "Scheduled by DCOS",
                                     int(time.time()),
                                     "unknown",
                                     "NDatanodes: {0} NSlaves: {1}".format(ndatanodes,nslaves))
        curl_node = list(self.masters)[0]
        self.workflow_injector.spark_standalone(curl_node,ndatanodes,nslaves)

    def cassandra_cluster_scenario(self,nnodes):
        self.write_to_experiment_log(current_milli_time(), "workflow", "cassandra_cluster", "Scheduled by DCOS",
                                     int(time.time()),
                                     "unknown",
                                     "NNodes: {0}".format(nnodes))
        curl_node = list(self.masters)[0]
        self.workflow_injector.cassandra_cluster(curl_node, nnodes)

    def ycsb_cassandra_client_scenario(self,ninstances,list_of_nodes,workload):
        self.write_to_experiment_log(current_milli_time(), "workflow", "ycsb_cassandra_client", "Scheduled by DCOS",
                                     int(time.time()),
                                     "unknown",
                                     "NInstances: {0} LNodes: {1} workload: {2}".format(ninstances,list_of_nodes,workload))
        curl_node = list(self.masters)[0]
        self.workflow_injector.ycsb_cassandra(curl_node, ninstances,list_of_nodes,workload)

    # This are the stress methods. We are going to write in the experiment log the type of anomaly
    # and the time when the mentioned anomaly started.

    def kill_container_id(self,node, containerid):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "killed container", node, int(time.time()),
                                     int(time.time()), "container ID: {0}".format(containerid))
        p = SshProcess('sudo docker kill {0}'.format(containerid),
                       host=node,
                       connection_params=self.connection_params).run()


    def stress_cpu_nodes(self, nodes, nstressors, timeout):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "stress_cpu_nodes", nodes, int(time.time()),
                                     int(time.time()) + timeout, "Stressors: {0}".format(nstressors))
        self.anomaly_injector.stress_cpu(nodes, nstressors, timeout)

    def stress_cpu_nodes_random(self, nnodes, nstressors, timeout,leave_out):
        list_nodes = list(self.private_agents.union(self.masters).difference(leave_out))
        shuffle(list_nodes)
        self.stress_cpu_nodes(set(list_nodes[0:nnodes]), nstressors, timeout)

    def stress_disk_nodes(self, nodes, nstressors, timeout):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "stress_disk_nodes", nodes, int(time.time()),
                                     int(time.time()) + timeout, "Stressors: {0}".format(nstressors))
        self.anomaly_injector.stress_disk(nodes, nstressors, timeout)

    def stress_disk_nodes_random(self, nnodes, nstressors, timeout,leave_out):
        list_nodes = list(self.private_agents.union(self.masters).difference(leave_out))
        shuffle(list_nodes)
        self.stress_disk_nodes(set(list_nodes[0:nnodes]), nstressors, timeout)

    def stress_network_nodes(self, nodes, nstressors, timeout):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "stress_network_nodes", nodes, int(time.time()),
                                     int(time.time()) + timeout, "Stressors: {0}".format(nstressors))
        self.anomaly_injector.stress_network(nodes, nstressors, timeout)

    def stress_network_nodes_random(self, nnodes, nstressors, timeout):
        list_nodes = list(self.private_agents.union(self.masters))
        shuffle(list_nodes)
        self.stress_network_nodes(set(list_nodes[0:nnodes]), nstressors, timeout)

    def stress_lockbus_nodes(self, nodes, nstressors, timeout):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "stress_lockbus_nodes", nodes, int(time.time()),
                                     int(time.time()) + timeout, "Stressors: {0}".format(nstressors))
        self.anomaly_injector.stress_lockbus(nodes, nstressors, timeout)

    def stress_lockbus_nodes_random(self, nnodes, nstressors, timeout):
        list_nodes = list(self.private_agents.union(self.masters))
        shuffle(list_nodes)
        self.stress_lockbus_nodes(set(list_nodes[0:nnodes]), nstressors, timeout)

    def stress_cache_nodes(self, nodes, nstressors, timeout):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "stress_cache_nodes", nodes, int(time.time()),
                                     int(time.time()) + timeout, "Stressors: {0}".format(nstressors))
        self.anomaly_injector.stress_cache(nodes, nstressors, timeout)

    def stress_cache_nodes_random(self, nnodes, nstressors, timeout):
        list_nodes = list(self.private_agents.union(self.masters))
        shuffle(list_nodes)
        self.stress_cache_nodes(set(list_nodes[0:nnodes]), nstressors, timeout)

    def stress_big_heap_nodes(self, nodes, nstressors, timeout):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "stress_big_heap_nodes", nodes, int(time.time()),
                                     int(time.time()) + timeout, "Stressors: {0}".format(nstressors))
        self.anomaly_injector.stress_big_heap(nodes, nstressors, timeout)

    def stress_big_heap_nodes_random(self, nnodes, nstressors, timeout,leave_out):
        list_nodes = list(self.private_agents.union(self.masters).difference(leave_out))
        shuffle(list_nodes)
        self.stress_big_heap_nodes(set(list_nodes[0:nnodes]), nstressors, timeout)

    def stress_matrix_nodes(self, nodes, nstressors, timeout):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "stress_matrix_nodes", nodes, int(time.time()),
                                     int(time.time()) + timeout, "Stressors: {0}".format(nstressors))
        self.anomaly_injector.stress_matrix(nodes, nstressors, timeout)

    def stress_matrix_nodes_random(self, nnodes, nstressors, timeout):
        list_nodes = list(self.private_agents.union(self.masters))
        shuffle(list_nodes)
        self.stress_matrix_nodes(set(list_nodes[0:nnodes]), nstressors, timeout)

    def stress_stream_memory_nodes(self, nodes, nstressors, timeout):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "stress_stream_memory_nodes", nodes, int(time.time()),
                                     int(time.time()) + timeout, "Stressors: {0}".format(nstressors))
        self.anomaly_injector.stress_stream_memory(nodes, nstressors, timeout)

    def stress_stream_memory_nodes_random(self, nnodes, nstressors, timeout):
        list_nodes = list(self.private_agents.union(self.masters))
        shuffle(list_nodes)
        self.stress_stream_memory_nodes(set(list_nodes[0:nnodes]), nstressors, timeout)

    def stress_zlib_nodes(self, nodes, nstressors, timeout):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "stress_zlib_nodes", nodes, int(time.time()),
                                     int(time.time()) + timeout, "Stressors: {0}".format(nstressors))
        self.anomaly_injector.stress_zlib(nodes, nstressors, timeout)

    def stress_zlib_nodes_random(self, nnodes, nstressors, timeout):
        list_nodes = list(self.private_agents.union(self.masters))
        shuffle(list_nodes)
        self.stress_zlib_nodes(set(list_nodes[0:nnodes]), nstressors, timeout)

    def limit_upload_bandwidth_nodes(self,nodes,delay='100ms',delay_jitter='1ms',bandwidth='100kbps',loss_percent='1%',timeout=10):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "limit_upload_bandwidth_nodes", nodes, int(time.time()),
                                     int(time.time()) + timeout, "delay:{0},delay_jitter:{1},bandwidth:{2},loss_percent:{3}".format(delay,delay_jitter,bandwidth,loss_percent))
        self.anomaly_injector.limit_bandwidth(nodes,delay,delay_jitter,bandwidth,loss_percent,timeout)

    def limit_upload_bandwidth_nodes_random(self,nnodes,leave_out,delay='100ms',delay_jitter='1ms',bandwidth='100kbps',loss_percent='1%',timeout=10):
        list_nodes = list(self.private_agents.union(self.masters).difference(leave_out))
        shuffle(list_nodes)
        self.limit_upload_bandwidth_nodes(set(list_nodes[0:nnodes]),delay,delay_jitter,bandwidth,loss_percent,timeout)

    def restore_upload_bandwidth_nodes(self,nodes):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "restore_upload_bandwidth", nodes, int(time.time()),
                                     0, "No info")
        self.anomaly_injector.restore_upload_bandwidth(nodes)

    def reboot_machine_nodes(self,nodes):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "reboot_machine_nodes", nodes, int(time.time()),
                                     0, "No info")
        self.anomaly_injector.reboot_machine(nodes)

    def shutdown_machine_nodes(self,nodes):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "shutdown_machine_nodes", nodes, int(time.time()),
                                     0, "No info")
        self.anomaly_injector.shutdown_machine(nodes)

    def fill_up_disk_nodes(self,nodes):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "fill_up_disk_nodes", nodes, int(time.time()),
                                     0, "No info")
        self.anomaly_injector.fill_up_disk(nodes)

    def clear_up_disk_nodes(self,nodes):
        self.write_to_experiment_log(current_milli_time(), "anomaly", "clear_up_disk_nodes", nodes, int(time.time()),
                                     0, "No info")
        self.anomaly_injector.clear_up_disk(nodes)

    def stress_endpoint(self,endpoint,ninstances,nclients,ntime,time_unit):
        curl_node = list(self.masters)[0]
        # we query the marathon-user API for some information about the load balancer
        p = SshProcess('curl "http://leader.mesos/service/marathon-user/v2/tasks"',
                       host=curl_node,
                       connection_params=self.connection_params).run()
        d = json.loads(p.stdout)
        marathon_lb_tasks = filter(lambda task: task['appId'] == u'/wordpresslb/loadbalancer/marathonlb',
                                   d.get('tasks'))
        # for the moment we are going to keep the host. Note how we don't need it currently but we can use some other
        # info in the future
        marathon_lb_host = marathon_lb_tasks[0]['host']
        unit_in_seconds = {"S" : 1 ,"M" : 60 ,"H" : 3600}
        self.write_to_experiment_log(current_milli_time(), "anomaly", "stress_endpoint", "marathon-lb.marathon.mesos",
                                     int(time.time()), int(time.time()) + (int(ntime) * unit_in_seconds[time_unit]),
                                     "EndPoint: {0} Instances: {1} Clients: {2} Time: {3}".format(endpoint,ninstances,nclients,str(ntime) + time_unit))
        self.anomaly_injector.stress_endpoint_siege(curl_node,endpoint,ninstances,nclients,str(ntime) + time_unit)

    def stress_endpoint_ab(self, endpoint, ninstances, nclients, nrequests, timein):
        curl_node = list(self.masters)[0]
        self.write_to_experiment_log(current_milli_time(), "anomaly", "stress_endpoint_ab", "marathon-lb.marathon.mesos",
                                     int(time.time()),int(time.time()) + timein,
                                     "EndPoint: {0} Instances: {1} Clients: {2} Requests: {3}".format(endpoint,ninstances,nclients,nrequests))
        self.anomaly_injector.ab_clients_stress(curl_node,endpoint,ninstances,nclients,nrequests)


