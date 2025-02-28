from simulator.node import Node
import json


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.distance_vector = {}   # key: node id          value: (cost of shortest path, shortest path list)
        self.outbound_links = {}    # key: neighbor id      value: cost to get to neighbor
        self.neighbor_DVs = {}      # key: neighbor id      value: (timestamp, most recent DV)
        
        self.distance_vector[self.id] = (0, [self.id])

    # Return a string
    def __str__(self):
        output = "Node " + str(self.id) + ": " + str(self.neighbors) + ", " + str(self.distance_vector)
        return output

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # if latency == -1, delete link
        if latency == -1:
            print("latency is -1")
            return
        
        # update outbound links
        self.outbound_links[neighbor] = latency

        # intialize neighbor in neighbors 
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)

        # initialize neighbor in DV (if not already in it)
        if neighbor not in self.distance_vector:
            self.distance_vector[neighbor] = (latency, [self.id, neighbor])

        # find shortest path to neighbor (either take existing path or new link)
        if neighbor not in self.neighbor_DVs:
            prev_cost = self.distance_vector[neighbor][0]
            new_cost = self.outbound_links[neighbor]
            if new_cost < prev_cost:
                self.distance_vector[neighbor] = (new_cost, [self.id, neighbor])

            assumed_dv = {}
            for node in self.distance_vector.keys():
                path = self.distance_vector[node][1]
                assumed_dv[node] = (float('inf'), path)

            self.neighbor_DVs[neighbor] = (self.get_time(), assumed_dv)
    
        # recalculate whole DV (outbound links changed)
        for node in self.distance_vector:
            if node != neighbor and node != self.id:
                cost, path = self.get_next_hop(node)
                self.distance_vector[node] = (cost, path)

        # send msg to neighbors
        msg_body = {
            "sender": self.id,
            "sent_dv": self.distance_vector,
            "timestamp": self.get_time(),
            "deleted_link": None
        }
        
        msg_to_send = json.dumps(msg_body)
        self.send_to_neighbors(msg_to_send)

    # Fill in this function
    def process_incoming_routing_message(self, m):
        # parse incoming message
        msg = json.loads(m)
        sender = msg["sender"]
        received_dv = {int(k): v for k, v in msg["sent_dv"].items()}
        timestamp = msg["timestamp"]
        deleted_link = msg["deleted_link"]
        
        # discard msg if it's old
        if sender in self.neighbor_DVs and self.neighbor_DVs[sender][0] > timestamp:
            return
        
        # updating neighbor DVs w/ most current DV (didn't trigger previous if statement)
        self.neighbor_DVs[sender] = (timestamp, received_dv)

        # handle deleted link msg
        if deleted_link is not None:
            print("link should be deleted")
            return
        
        
        # initialize sender in DV (if not already in it)
        latency = received_dv[self.id][0]
        if sender not in self.distance_vector:
            self.distance_vector[sender] = (latency, [self.id, sender])
        
        if sender not in self.outbound_links:
            self.outbound_links[sender] = latency

        if sender not in self.neighbors:
            self.neighbors.append(sender)
        
        # calculate DV (neighbor DVs changed)
        new_dv = { node : (0, [node]) for node in self.distance_vector }
        for node in new_dv:
            cost, path = self.get_next_hop(node)
            new_dv[node] = (cost, path)

        # if new_dv != self.distance_vector, send your DV out
        if new_dv != self.distance_vector:
            self.distance_vector = new_dv
            msg_body = {
                "sender": self.id,
                "sent_dv": self.distance_vector,
                "timestamp": self.get_time(),
                "deleted_link": None
            }
            
            msg_to_send = json.dumps(msg_body)
            self.send_to_neighbors(msg_to_send)

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        dsts, prvs = self.shortest_path()
        if destination not in dsts:
            return -1
        
        path = []
        curr = destination
        while prvs[curr] != curr:
            path.append(curr)
            curr = prvs[curr]
        path.append(self.id)

        return dsts[destination], path[::-1]
    
    # Bellman-Ford - self.outbound_links and self.neighbor_DVs
    def shortest_path(self):
        dsts = {}
        prvs = {}

        vertices = self.distance_vector.keys()
        for vertex in vertices:
            dsts[vertex] = float('inf')
            prvs[vertex] = None

        dsts[self.id] = 0

        for vertex in vertices:
            min_cost = self.distance_vector[vertex][0]
            path = self.distance_vector[vertex][1]
            if len(path) == 1:
                min_neighbor = vertex
            else:
                min_neighbor = path[0]

            for neighbor in self.neighbors:
                print(self.neighbor_DVs[neighbor])
                new_cost = self.outbound_links[neighbor] + self.neighbor_DVs[neighbor][1][vertex][0]
                if new_cost < min_cost:
                    min_cost = new_cost
                    min_neighbor = neighbor
                    
            dsts[vertex] = min_cost
            prvs[vertex] = min_neighbor

        return dsts, prvs