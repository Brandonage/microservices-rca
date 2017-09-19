from execo import Remote


"""
This class is going to inject anomalies on the different nodes and Docker containers. Is not going to have an internal
state of the nodes. The nodes are going to be just parameters to the functions.
Another thing is that the implementation is going to be different depending on the underneath testbed (e.g. vagrant,
g5k, Amazon). We leave open the possibility of using a Bridge pattern and leave the implementation as other abstraction
For the moment we only focus on DC/OS
"""

class AnomalyInjectorDCOS():
    def __init__(self,nodes,connection_params):
        # From now on these are the connection params we will use
        self.connection_params = connection_params
        self.nodes = nodes
        # The anomaly injector needs some underlying software that is going to install when instatiated
        Remote(cmd='sudo yum -y install epel-release && sudo yum repolist',
               hosts=nodes,
               connection_params=connection_params).run()
        Remote(cmd='sudo yum -y install stress-ng',
               hosts=nodes,
               connection_params=connection_params).run()

    def stress_cpu(self,nodes,nstressors,time):
        Remote(cmd="stress-ng --cpu {0} --timeout {1}s".format(nstressors,time),
               hosts=nodes,
               connection_params=self.connection_params
               ).start()
