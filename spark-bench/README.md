**How to run the container** 

The CORE_CONF_fs_defaultFS and YARN_CONF_yarn_resourcemanager_hostname variables are needed in order to connect the 
spark-bench with the yarn resouce manager and hdfs namenode. 

Note that there is one environmental variables that are already set in the Dockerfile:
- SPARK_HOME = this is the folder of the spark installation. It's actually set up in the uhopper/hadoop-spark image and 
not in this one. Its function is 
to take the libraries and jars needed to be included in the spark-submit.
(SPARK_MASTER_HOST was set before. Now left open to be changed in the minimal-example.conf file to choose between yarn or spark standalone)

An example on how to run this docker image with a bash. From the bash we can executes one of the several workloads

docker run -it -e SPARK_MASTER_HOST=spark://10.136.16.180:6529/ -e MULTIHOMED_NETWORK=0 -e HDFS_CONF_dfs_datanode_use_datanode_hostname=false -e HDFS_CONF_dfs_namenode_datanode_registration_ip___hostname___check=false -e HDFS_CONF_dfs_client_use_datanode_hostname=false -e HDFS_CONF_dfs_datanode_use_datanode_ip_hostname=false -e CORE_CONF_fs_defaultFS=hdfs://namenode-namenode-hdfsspark.marathon-user.containerip.dcos.thisdcos.directory:8020 -e YARN_CONF_yarn_resourcemanager_hostname=resourcemanager-resourcemanager-hdfsspark.marathon-user.containerip.dcos.thisdcos.directory alvarobrandon/spark-bench /bin/bash
_(Inside the Docker container console)_

./bin/spark-bench.sh ./examples/minimal-example.conf

./bin/spark-shell --master spark://10.136.35.160:24867