FROM bde2020/spark-base:2.1.0-hadoop2.8-hive-java8

ENV SPARK_BENCH_URL https://github.com/SparkTC/spark-bench/releases/download/v91/spark-bench_2.1.1_0.3.0-RELEASE_91.tgz


RUN curl -fSL "$SPARK_BENCH_URL" -o /tmp/spark-bench.tgz \
    && tar -xvzf /tmp/spark-bench.tgz -C /opt \
    && mv /opt/spark-bench* /opt/spark-bench \
    && rm -f /tmp/spark-bench-tar.gz \
    && apt-get -y install vim

ADD workload_parquet.conf /opt/spark-bench/examples

WORKDIR /opt/spark-bench