class Factory:

    def __init__(self):
        self._controllers = {}
        self._nodes = {}

    def register_nodes(self, node, controllerCreator, nodeCreator):
        self._controllers[node] = controllerCreator
        self._nodes[node] = nodeCreator

    def get_controller(self, controller):
        creator = self._nodes.get(controller)
        if not creator:
            raise ValueError(controller)
        return creator

    def get_node(self, node):
        creator = self._nodes.get(node)
        if not creator:
            raise ValueError(node)
        return creator


nuvo_factory = Factory()
