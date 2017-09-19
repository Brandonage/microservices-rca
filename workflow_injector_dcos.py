from execo import Put, SshProcess
from common_functions import replace_infile
import os

"""
This class is going to start typical dcos_workflows of containers on a DCOS cluster. Is not going to have an internal
state of the nodes. The nodes are going to be just parameters to the functions.
The only parameter it needs are some connection parameters to execute the execo instructions.
We opt for uploading the JSON file with the workflow to the nodes in vagrant and post to the API from there. We do so
in order to use the DNS of Mesos to curl the http://leader.mesos directly without knowing the IP of the leader
"""

class WorkflowInjectorDCOS():
    def __init__(self,nodes,connection_params,):
        # From now on these are the connection params we will use
        self.connection_params = connection_params
        self.nodes = nodes
        self.resources_path = os.path.join(os.path.dirname(__file__),'dcos_workflows')

    def send_exec_to_marathon(self,curl_node):
        Put(hosts=curl_node,
            local_files=[self.resources_path + "/exec.json"],
            remote_location="/home/vagrant/exec.json",
            connection_params=self.connection_params).run()
        p = SshProcess(
            'curl -X POST "http://leader.mesos/service/marathon-user/v2/groups" -H "content-type: application/json" -d@/home/vagrant/exec.json',
            host=curl_node,
            connection_params=self.connection_params).run()

    def kafka_producers_and_consumers(self,masters,nbrokers,nconsumers,nproducers):
        curl_node = list(masters)[0]
        replacements = {"@nbrokers@" : str(nbrokers),"@nconsumers@" : str(nconsumers), "@nproducers@" : str(nproducers)}
        replace_infile(self.resources_path + "/kafka_consum_prod.json",self.resources_path + "/exec.json",replacements)
        self.send_exec_to_marathon(curl_node)
