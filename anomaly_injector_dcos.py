from execo import Remote, Put, SshProcess
from time import sleep
from common_functions import replace_infile
import os

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
        # and it will also use the workflows available for dcos, specially the siege workflow to generate a big ammount
        # of calls to an endpoint
        self.resources_path = os.path.join(os.path.dirname(__file__), 'dcos_workflows')
        # we upload a file that will be used by the siege container to generate requests to an endpoint
        Put(hosts=nodes,
            local_files=[self.resources_path + "/siegerc"],
            remote_location="/home/vagrant/siegerc",
            connection_params=self.connection_params).run()


    def send_exec_to_marathon(self,curl_node):
        Put(hosts=curl_node,
            local_files=[self.resources_path + "/exec.json"],
            remote_location="/home/vagrant/exec.json",
            connection_params=self.connection_params).run()
        p = SshProcess(
            'curl -X POST "http://leader.mesos/service/marathon-user/v2/groups" -H "content-type: application/json" -d@/home/vagrant/exec.json',
            host=curl_node,
            connection_params=self.connection_params).run()

    def stress_ng(self,type,nstressors,timeout,nodes):
        Remote(cmd="stress-ng --{0} {1} --timeout {2}s".format(type,nstressors,timeout),
               hosts=nodes,
               connection_params=self.connection_params
               ).start()

    def stress_cpu(self,nodes,nstressors,timeout):
        self.stress_ng(type='cpu',nstressors=nstressors,timeout=timeout,nodes=nodes)

    def stress_disk(self,nodes,nstressors,timeout):
        self.stress_ng(type='hdd', nstressors=nstressors, timeout=timeout, nodes=nodes)

    def stress_network(self,nodes,nstressors,timeout):
        self.stress_ng(type='sock', nstressors=nstressors, timeout=timeout, nodes=nodes)

    def stress_lockbus(self,nodes,nstressors,timeout):
        """
        N stressors that rapidly lock and increment 64 bytes of randomly chosen memory from a 16MB mmap d region
        (Intel x86 CPUs only). This will cause cacheline misses and stalling of CPUs.
        :param nodes:
        :param nstressors:
        :param time:
        """
        self.stress_ng(type='lockbus', nstressors=nstressors, timeout=timeout, nodes=nodes)

    def stress_cache(self,nodes,nstressors,timeout):
        """
        start N stressors that perform random wide spread memory read and writes to thrash the CPU cache. The code does
        not intelligently determine the CPU cache configuration and so it may be sub-optimal in producing hit-miss
        read/write activity for some processors.
        :param nodes:
        :param nstressors:
        :param time:
        """
        self.stress_ng(type='cache', nstressors=nstressors, timeout=timeout, nodes=nodes)

    def stress_big_heap(self,nodes,nstressors,timeout):
        """
        start N workers that grow their heaps by reallocating memory. If the out of memory killer (OOM) on Linux kills
        the worker or the allocation fails then the allocating process starts all over again. Note that the OOM
        adjustment for the worker is set so that the OOM killer will treat these workers as the first candidate
        processes to kill.
        :param nodes:
        :param nstressors:
        :param time:
        """
        self.stress_ng(type='bigheap', nstressors=nstressors, timeout=timeout, nodes=nodes)

    def stress_matrix(self,nodes,nstressors,timeout):
        """
        start N workers that perform various matrix operations on floating point values. Testing on 64 bit x86 hardware
        shows that this provides a good mix of memory, cache and floating point operations and is an excellent way to
        make a CPU run hot. By default, this will exercise all the matrix stress methods one by one.
        :param nodes:
        :param nstressors:
        :param time:
        """
        self.stress_ng(type='matrix', nstressors=nstressors, timeout=timeout, nodes=nodes)

    def stress_stream_memory(self,nodes,nstressors,timeout):
        """
        start N workers exercising a memory bandwidth stressor loosely based on the STREAM "Sustainable Memory
        Bandwidth in High Performance Computers" benchmarking tool by John D. McCalpin, Ph.D.
        This stressor allocates buffers that are at least 4 times the size of the CPU L2 cache and continually
        performs rounds of computations on large arrays of double precision floating point numbers
        :param nodes:
        :param nstressors:
        :param time:
        """
        self.stress_ng(type='stream', nstressors=nstressors, timeout=timeout, nodes=nodes)

    def stress_zlib(self,nodes,nstressors,timeout):
        """
        start N workers compressing and decompressing random data using zlib. Each worker has two processes, one that
        compresses random data and pipes it to another process that decompresses the data.
        This stressor exercises CPU, cache and memory.
        :param nodes:
        :param nstressors:
        :param time:
        """
        self.stress_ng(type='zlib', nstressors=nstressors, timeout=timeout, nodes=nodes)

    def limit_upload_bandwidth(self,nodes,delay='100ms',delay_jitter='1ms',bandwidth='100kbps',loss_percent='1%'):
        Remote(cmd='sudo tc qdisc add dev eth0 root handle 1: htb default 10',
               hosts=nodes,
               connection_params=self.connection_params).run()
        Remote(cmd='sudo tc class add dev eth0 parent 1: classid 1:10 htb rate {0} ceil {0}'.format(bandwidth),
               hosts=nodes,
               connection_params=self.connection_params).run()
        Remote(cmd='sudo tc qdisc add dev eth0 parent 1:10 handle 10: netem delay {0} {1} 25% loss {2}'.format(delay,delay_jitter,loss_percent),
               hosts=nodes,
               connection_params=self.connection_params).run()
        # sudo tc qdisc add dev eth0 root handle 1: htb default 10
        # sudo tc class add dev eth0 parent 1: classid 1:10 htb rate 10kbps ceil 10kbps
        # sudo tc qdisc add dev eth0 parent 1:10 handle 10: netem delay 100ms 0.1ms 25% loss 1%

    def restore_upload_bandwidth(self,nodes):
        Remote(cmd='sudo tc qdisc del dev eth0 root',
               hosts=nodes,
               connection_params=self.connection_params).run()

    def limit_bandwidth(self,nodes,delay='100ms',delay_jitter='1ms',bandwidth='100kpbs',loss_percent='1%',timeout=10):
        self.limit_upload_bandwidth(nodes,delay,delay_jitter,bandwidth,loss_percent)
        sleep(timeout)
        self.restore_upload_bandwidth(nodes)

    def reboot_machine(self,nodes):
        Remote(cmd='sudo reboot',
               hosts=nodes,
               connection_params=self.connection_params).run()

    def shutdown_machine(self,nodes):
        Remote(cmd='sudo shutdown',
               hosts=nodes,
               connection_params=self.connection_params).run()

    def fill_up_disk(self,nodes):
        Remote(cmd="dd if=/dev/zero of=/tmp/tempFiller.deleteMe bs=1M count=1M",
               host=nodes,
               connection_params=self.connection_params).run()

    def clear_up_disk(self,nodes):
        Remote(cmd="rm /tmp/tempFiller.deleteMe",
               host=nodes,
               connection_params=self.connection_params).run()

    def stress_endpoint_siege(self, curl_node, endpoint,ninstances,nclients,time):
        replacements = {"@delay@" : str(1),
                        "@time@": str(time),
                        "@nclients@": str(nclients),
                        "@endpoint@": endpoint,
                        "@ninstances@": str(ninstances)
                        }
        # we have a different json file for the siege stress to avoid having same marathon group names as the normal
        # siege clients workflow
        replace_infile(self.resources_path + "/siege_stress.json",self.resources_path + "/exec.json",replacements)
        self.send_exec_to_marathon(curl_node)

