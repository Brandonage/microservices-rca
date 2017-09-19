from anomaly_injector_dcos import AnomalyInjectorDCOS


def get_anomaly_injector(orchestrator,nodes,connection_params):
    if orchestrator=="dcos":
        return AnomalyInjectorDCOS(nodes,connection_params,)