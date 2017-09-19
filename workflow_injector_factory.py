from workflow_injector_dcos import WorkflowInjectorDCOS


def get_workflow_injector(orchestrator, nodes, connection_params):
    if orchestrator=="dcos":
        return WorkflowInjectorDCOS(nodes,connection_params)