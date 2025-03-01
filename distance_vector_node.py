from simulator.node import Node
import json
import copy


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.distance_vector = {}   # key: node id          value: (cost of shortest path, shortest path list)
        self.outbound_links = {}    # key: neighbor id      value: cost to get to neighbor
        self.neighbor_DVs = {}      # key: neighbor id      value: most recent DV
        self.node_messages = {}     # key: neighbor id      value: timestamp
        
        self.distance_vector[self.id] = (0, [self.id])

    # Return a string
    def __str__(self):
        output = "Node " + str(self.id) + ": " + str(self.neighbors) + ", " + str(self.distance_vector)
        return output

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # update outbound links, if latency == -1, delete link
        if latency == -1:
            del self.outbound_links[neighbor]
            del self.neighbor_DVs[neighbor]
        else:
            self.outbound_links[neighbor] = latency

        # intialize neighbor in neighbors
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)

        # update outbound links
        for neighbor in self.outbound_links:
            self.distance_vector[neighbor] = (latency, [self.id, neighbor])

        old_dv = copy.deepcopy(self.distance_vector)

        # recompute personal DV
        dsts, prvs = self.shortest_path()

        # send msg to neighbors
        if old_dv != self.distance_vector:
            msg_body = {
                "sender": self.id,
                "sent_dv": self.distance_vector,
                "timestamp": self.get_time(),
            }

            msg_to_send = json.dumps(msg_body)
            self.send_to_neighbors(msg_to_send)

    # Fill in this function
    def process_incoming_routing_message(self, m):
        # parse incoming message
        msg = json.loads(m)
        # print(f"node {self.id} received this message:")
        # print(msg)
        # print("***")
        sender = msg["sender"]
        received_dv = {int(k): v for k, v in msg["sent_dv"].items()}
        timestamp = msg["timestamp"]

        changes = False

        if sender not in self.neighbor_DVs:
            self.neighbor_DVs[sender] = {}

        # if the message is old, discard it
        if sender in self.node_messages and timestamp < self.node_messages[sender]:
            return

        outdated_neighbors = []

        for neighbor in self.neighbor_DVs:
            outdated_neighbors.append(neighbor)

        for vertex in received_dv:
            if vertex in outdated_neighbors:
                outdated_neighbors.remove(vertex)
            cost = received_dv[vertex][0]
            path = received_dv[vertex][1]
            if vertex in self.neighbor_DVs[sender]:
                if self.id in path:
                    del self.neighbor_DVs[sender][vertex]
                    changes = True
                else:
                    self.neighbor_DVs[sender][vertex] = (cost, path)
            else:
                if self.id not in path:
                    self.node_messages[sender] = timestamp
                    self.neighbor_DVs[sender][vertex] = (cost, path)
                    changes = True

        for neighbor in outdated_neighbors:
            print(self.neighbor_DVs[sender])
            del self.neighbor_DVs[sender][neighbor]
            changes = True

        self.node_messages[sender] = timestamp

        if changes:
            old_dv = copy.deepcopy(self.distance_vector)

            # recompute personal DV
            dsts, prvs = self.shortest_path()

            # send msg to neighbors
            if old_dv != self.distance_vector:
                msg_body = {
                    "sender": self.id,
                    "sent_dv": self.distance_vector,
                    "timestamp": self.get_time(),
                }   

                msg_to_send = json.dumps(msg_body)
                self.send_to_neighbors(msg_to_send)

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if destination in self.distance_vector:
            if self.distance_vector[destination][0] < float('inf'):
                return copy.deepcopy(self.distance_vector[destination][1])[1]

        return -1

    # Bellman-Ford - self.outbound_links and self.neighbor_DVs
    def shortest_path(self):
        dsts = {}
        prvs = {}

        self.distance_vector = {}

        for neighbor in self.outbound_links:
            self.distance_vector[neighbor] = (self.outbound_links[neighbor], [self.id, neighbor])
        
        for neighbor in self.neighbor_DVs:
            for vertex in self.neighbor_DVs[neighbor]:
                if neighbor in self.outbound_links:
                    new_cost = self.neighbor_DVs[neighbor][vertex][0] + self.outbound_links[neighbor]
                    if vertex not in self.distance_vector or (vertex in self.distance_vector and new_cost < self.distance_vector[vertex][0]):
                        new_path = [self.id] + copy.deepcopy(self.neighbor_DVs[neighbor][vertex][1])
                        self.distance_vector[vertex] = (new_cost, new_path)

        return dsts, prvs