import anomaly_injector_factory
import workflow_injector_factory

"""
This is the main class that is going to start and inject the failures on the DCOS cluster
"""
class MicroServicesRCA():
    def __init__(self,masters,public_agents,connection_params,orchestrator):
        # I dont know if we really need the master IP when we have the leader.mesos name to locate it
        # All and all there are three options: give to it one master, several masters, or None and just use
        # the leader.mesos name resolution with any of the slaves. I suppose this DNS also applies to K8
        """

        :param master:
        :param slaves:
        :param connection_params:
        """
        self.masters = masters
        # We need all the slaves in order to do things like inject delay between two random nodes
        self.public_agents = public_agents
        # This is going to be the anomaly injector. Is going to have as a parameter some connection parameters for execo
        # We are going to have only one, but we could have more than one if we wanted to inject failures at different
        # levels. e.g. an anomaly injector at physical level, another at VM level, another on some other cluster with different
        # credentials and so on... for the sake of simplicity only one here
        # we also pass as a parameter the nodes of the cluster since we need to install some software on them to
        # generate these anomalies
        self.anomaly_injector = anomaly_injector_factory.get_anomaly_injector(orchestrator, masters.union(public_agents), connection_params)
        # same as the anomaly injector. But this one is going to inject workflows
        self.workflow_injector = workflow_injector_factory.get_workflow_injector(orchestrator,masters.union(public_agents),connection_params)

    # From here we are going to include the scenarios that inject both workloads and anomalies. We decided to keep
    # this logic here in the MicroServicesRCA object instead of calling directly the injectors functions.
    # (e.g. microservices_rca.anomaly_injector.kill_node('192.167.143.12') The reason is that we might need to use both
    # injectors to create some scenarios. Anyways we also have the option of using the injectors but we will try to
    # keep as much logic here as possible

    def kafka_producer_consumer_scenario(self,nbrokers,nconsumers,nproducers):
        self.workflow_injector.kafka_producers_and_consumers(self.masters,nbrokers,nconsumers,nproducers)

    def stress_cpu_nodes(self,nodes, nstressors, time):
        self.anomaly_injector.stress_cpu(nodes,nstressors,time)