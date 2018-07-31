# microservices-rca
A tool to start microservice architectures in DCOS and inject failures for Root cause analysis purposes

## Usage

Using this project to create your own experiments is very easy. 

As a prerequisite, DCOS has to be installed in a 
cluster in G5K. The project (https://github.com/Brandonage/execo-utilities-g5k) provides methods to install DCOS in a simple and scripted way.

The MicroServicesRCA class is the one that provides all the methods to start microservice architectures and to inject anomalies 
in the infrastructure. We just need to create it with the following parameters:

1. masters: A set which contains the addresses of the DCOS masters. 
2. private_agents: A set which contains the addresses of the DCOS private agents.
3. public_agents: A set which contains the addresses of the DCOS public agents.
4. connection_params: A dictionary with the execo connection configuration
5. orchestrator: the orchestrator of choice to deploy the microservice architecture. At the moment only DCOS is available
6. experiment_log: A dataframe where all the different events in the experiment are going to be registered. The dataframe 
has to have the following columns.
```python
experiment_log_dataframe  = pd.DataFrame(columns=["type","event","nodes","date_start","date_end","aditional_info","read_date"])
```


```python
testbed = MicroServicesRCA(masters={'128.128.128.128'},
                           private_agents={'1.1.1.1','2.2.2.2','3.3.3.3'},
                           public_agents={4.4.4.4},
                           connection_params=execo.config.default_connection_params,
                           orchestrator='dcos',
                           experiment_log=experiment_log_dataframe
          )
```

Once created we just have to trigger the events needed for the experiment. Example:

```python
# Start an kafka queue with 3 brokers and 7 producers pushing messages to the queue and 7 consumers reading them
testbed.kafka_producer_consumer_scenario(nbrokers=3,nconsumers=7,nproducers=7) 
# Stress the CPU of the nodes '10.136.5.73' and '10.136.5.75' with 6 stressors for 20 seconds
testbed.stress_cpu_nodes(nodes={'10.136.5.73', '10.136.5.75'}, nstressors=6,timeout=20)
```

## Microservice architectures available

- Kafka queue with producers and consumers: Spin up a kakfa queue with nbrokes, nconsumers and nproducers

```python
testbed.kafka_producer_consumer_scenario(nbrokers=3,nconsumers=7,nproducers=7) 
```

- HAProxy balancing load between nwordpress
```python
testbed.lb_wordpress_scenario(nwordpress=7)
```

- Clients that continuosly perform HTTP request to a backend. This can be used in conjuction with the HAproxy architecture
to test its loadbalancing capabilities. It uses Apache HTTP server benchmarking tool (https://httpd.apache.org/docs/2.4/programs/ab.html)
to create the clients that are going to perform the HTTP requests
    - endpoint: The URL of the endpoint
    - ninstances: How many of the Apache instances we are going to create
    - nclients: Inside each one of the instances, how many different clients we want to emulate
    - nrequests: how many HTTP requests each Apache instance should fulfill before dying
```python
testbed.ab_clients_scenario(endpoint="marathonlb-loadbalancer-wordpresslb.marathon-user.containerip.dcos.thisdcos.directory:10001",
                            ninstances=2,
                            nclients=10,
                            nrequests=15)
``` 

- HDFS cluster with ndatanodes and nnodemanagers
```python
testbed.hadoop_cluster_scenario(ndatanodes=3,nnodemanagers=3)
```
- Spark standalone + HDFS deployment with ndatanodes for HDFS and nslaves for spark

```python
testbed.spark_standalone_scenario(ndatanodes=4,nslaves=5)
```

- Cassandra cluster with nnodes

```python
testbed.cassandra_cluster_scenario(nnodes=5)
```

- A set of Yahoo Cloud Service Benchmark to send requests to the Cassandra cluster

```python
testbed.ycsb_cassandra_client_scenario(ninstances=4,list_of_nodes={'1.1.1.1','2.2.2.2','3.3.3.3'},workload='workloada')
```

## Anomalies to inject

- The following calls are used to kill or pause a container with a Docker `containerid` running on the server's IP `node`
    - ```testbed.kill_container_id(node, containerid)```
    - ```testbed.pause_container_id(node, containerid,timeout)```
- The following calls are used to stress the physical machines that form part of the cluster. To do that stress-ng has to be installed in the nodes of the cluster
nodes are the list of server's IP. eg. ```nodes={'1.1.1.1','2.2.2.2','3.3.3.3'}```, nstressors are the number of stress-ng stressors to use e.g. ```nstressors=6``` and timeout is the time window during which the machines should be stressed e.g. ```timeout=120```     
    - ```testbed.stress_cpu_nodes(nodes, nstressors, timeout)```
    - ```testbed.stress_disk_nodes(nodes, nstressors, timeout)```
    - ```testbed.stress_network_nodes(nodes, nstressors, timeout)```
    - ```testbed.stress_lockbus_nodes(nodes, nstressors, timeout)```
    - ```testbed.stress_cache_nodes(nodes, nstressors, timeout)```
    - ```testbed.stress_big_heap_nodes(nodes, nstressors, timeout)```
    - ```testbed.stress_matrix_nodes(nodes, nstressors, timeout)```
    - ```testbed.stress_stream_memory_nodes(nodes, nstressors, timeout)```
    - ```testbed.stress_zlib_nodes(nodes, nstressors, timeout)```
- The following call limits the bandwidth on a series of nodes. It uses ```tc``` to achieve this. The parameters passed to the function are the same ones as the ones specfied in ```tc``` documentation (https://linux.die.net/man/8/tc)
    - ```testbed.limit_upload_bandwidth_nodes(nodes,delay='100ms',delay_jitter='1ms',bandwidth='100kbps',loss_percent='1%',timeout=10)```
