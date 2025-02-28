from simulator.node import Node
import json


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.distance_vectors = {} # key: neighbor (int), val: (cost, next_hop) 
        self.edges = {} # key: (src, dst) (tuple of ints), val: cost (int)
        self.all_dvs = {} # key: neighbor (int), val: (timestamp, neighbor's DV)
        self.timestamp = 0
        self.distance_vectors[self.id] = (0, [])

    # Return a string
    def __str__(self):
        output = "Node " + str(self.id) + ": " + str(self.neighbors) + ", " + str(self.distance_vectors)
        return output

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        if latency == -1:
            if neighbor in self.neighbors:
                self.neighbors.remove(neighbor)

            self.edges.pop(frozenset({self.id, neighbor}), None)

            # msg_body = {
            #     "origin": self.id,
            #     "deleted_link": f"{self.id},{neighbor}"
            # }

            # msg_to_send = json.dumps(msg_body)
            # self.send_to_neighbors(msg_to_send)
            return
        
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)

        edge = frozenset({self.id, neighbor})
        self.edges[edge] = latency
        self.distance_vectors[neighbor] = (latency, [neighbor])

        msg_body = {
            "sender": self.id,
            "origin": self.id,
            "DV": self.distance_vectors,
            "timestamp": self.get_time(),
            "neighbor": neighbor,
            "latency": latency
        }

        msg_to_send = json.dumps(msg_body)
        self.send_to_neighbors(msg_to_send)

    # Fill in this function
    def process_incoming_routing_message(self, m):
        no_changes = True
        msg = json.loads(m)
        
        # extract headers from msg
        sender = msg["sender"] 
        origin = msg["origin"]
        DV = {int(k): v for k, v in msg["DV"].items()}
        neighbor = msg["neighbor"]
        latency = msg["latency"]
        timestamp = msg["timestamp"]

        # if we're receiving a neighbor's DV, store it
        # if (sender == origin or origin in self.neighbors) and (origin in self.neighbor_dvs and DV != self.neighbor_dvs[origin]):
        if sender not in self.all_dvs or self.all_dvs[sender][1] != DV or timestamp > self.all_dvs[sender][0]:
            if sender not in self.all_dvs:
                1+1
            elif self.all_dvs[sender][1] != DV:
                print("start")
                print(DV)
                print(self.all_dvs[sender])
            no_changes = False
            self.all_dvs[sender] = (timestamp, DV)

        # check if its a neighbor (before for loop), set its cost in self.distance_vectors immediately
        if sender in self.neighbors:
            self.distance_vectors[sender] = (self.edges[frozenset({self.id, sender})], [sender])
        
        # check if there are changes
        # edge = frozenset({origin, neighbor})
        # if edge not in self.edges or self.edges[edge] != latency:
        #     no_changes = False
        #     self.edges[edge] = latency

        for node in DV:
            # case 1: node not in self's DV
            # if node not in self.distance_vectors:
            #     no_changes = False
            #     self.distance_vectors[node] = (DV[node][0] + latency, self.get_next_hop(node))
                
            # case 2: potential path is shorter than current one in self's DV
            # print(node)
            # print(sender)
            # potential_path = DV[node][0] + self.distance_vectors[sender][0]
            # if potential_path < self.distance_vectors[node][0]:
            #     no_changes = False
            #     self.distance_vectors[node] = (potential_path, sender)   
            received_cost = DV[node][0]
            link_cost = self.edges.get(frozenset({self.id, sender}), float('inf'))

            if node == self.id:
                continue

            if node not in self.distance_vectors or (received_cost + link_cost) < self.distance_vectors[node][0]:
                no_changes = False
                self.distance_vectors[node] = (received_cost + link_cost, self.get_full_path(node))  
                
        # if any changes, send msg
        print(self.distance_vectors[origin])
        if not no_changes or (origin in self.distance_vectors and self.id in self.distance_vectors[origin][1]):
            msg_body = {
                "sender": self.id,
                "origin": origin,
                "DV": self.distance_vectors,
                "timestamp": timestamp,
                "neighbor": neighbor,
                "latency": latency
            }
            msg_to_send = json.dumps(msg_body)
            self.send_to_neighbors(msg_to_send)

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        dsts, prvs = self.shortest_path()
        if destination not in dsts or dsts[destination] == float('inf'):
            return -1
        
        curr = destination
        while prvs[curr] != self.id:
            curr = prvs[curr]
        return curr
    
    def get_full_path(self, destination):
        dsts, prvs = self.shortest_path()
        if destination not in dsts or dsts[destination] == float('inf'):
            print("get full path")
            return []
        
        path = []
        curr = destination
        while prvs[curr] != self.id:
            path.append(curr)
            curr = prvs[curr]
        path.append(curr)
        if path == None:
            print("FAIFOEIJOJFSOEIJOIFEIJSF")
        return path[::-1]

    # Bellman-Ford
    def shortest_path(self):
        dsts = {}
        prvs = {}

        source = self.id
        vertices = self.distance_vectors.keys()

        for vertex in vertices:
            dsts[vertex] = float('inf')
            prvs[vertex] = None
        
        dsts[source] = 0

        for _ in range(len(vertices) - 1):
            for edge in self.edges:
                src, dst = tuple(edge)
                alt = dsts[src] + self.edges[edge]
                if alt < dsts[dst]:
                    dsts[dst] = alt
                    prvs[dst] = src
        
        return dsts, prvs
    """
    INPUTS: vertices, edges, and source
    
    // Initialization
    for each vertex v in vertices:
        dist[v] := INFINITY      // Initially, vertices have infinite weight
        prev[v] := NULL          // and a null predecessor.
    dist[source] := 0            // Distance from source to itself is zero
    
    // Relax edges repeatedly.
    for i from 1 to size(vertices)-1:
        for each edge (u,v):
            alt := dist[u] + (u,v).cost() 
            if alt < dist[v]:
                dist[v] := alt
                prev[v] := u
    
    // outputs are distance and predecessor arrays   
    return dist[], prev[]
    """