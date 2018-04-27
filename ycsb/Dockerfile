FROM openjdk:alpine
RUN apk add --no-cache curl
RUN curl -O --location https://github.com/brianfrankcooper/YCSB/releases/download/0.12.0/ycsb-0.12.0.tar.gz
RUN tar xfvz ycsb-0.12.0.tar.gz
ENTRYPOINT ["ycsb-0.12.0/bin/ycsb.sh"]
WORKDIR /
CMD ["load","cassandra-cql","-P","ycsb-0.12.0/workloads/workloada"]






