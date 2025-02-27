from simulator.node import Node, Link
import json
import heapq

class Link_State_Node(Node):

    def __init__(self, id):
        super().__init__(id)
        self.router_graph = {} # adj matrix - key: (src, dst) -> val: cost
        self.node_messages = {} # key: node id, val: seq num
        self.seq_num = 0

    # Return a string
    def __str__(self):
        output = "Node " + str(self.id) + ": " + str(self.neighbors) + ", " + str(self.router_graph)
        return output

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # new node (its seq_num = 0) -> give all information (broadcast all of your link states to them)
        # if previous link but now its -1 (removed but now coming back in -> missed prior broadcasts)
        # both cases: resend all info
        # latency = -1 if delete a link

        if latency == -1:
            self.neighbors.remove(neighbor)
            cond_lat = float('inf')
        else:
            if neighbor not in self.neighbors:
                self.neighbors.append(neighbor)
            cond_lat = latency

        self.router_graph[f"{self.id},{neighbor}"] = cond_lat
        self.router_graph[f"{neighbor},{self.id}"] = cond_lat

        msg_body = {
            "router_graph": self.router_graph,
            "origin": self.id,
            "seq_num": self.seq_num
        }

        self.seq_num += 1

        msg_to_send = json.dumps(msg_body)
        self.send_to_neighbors(msg_to_send)

    # Fill in this function
    def process_incoming_routing_message(self, m):
        # when receiving updated info, forward it to all neighbors
        msg = json.loads(m)
        # print(str(self.id) + " received a message from " + str(msg["origin"]))
        routing_table = msg["router_graph"]
        origin = msg["origin"]
        seq_num = msg["seq_num"]

        for edge in routing_table:
            src, dst = map(int, edge.split(","))
            self.router_graph[f"{src},{dst}"] = routing_table[edge]
            self.router_graph[f"{dst},{src}"] = routing_table[edge]

        # if self.id in msg["visited"]: 
        #     return

        # new_visited = msg["visited"].copy()
        # new_visited.append(self.id)
            
        # msg_body = {
        #     "src": msg["src"],
        #     "dst": msg["dst"],
        #     "visited": new_visited,
        #     "lat": msg["lat"]
        # }
        if origin in self.node_messages and seq_num <= self.node_messages[origin]:
            return
        
        self.node_messages[origin] = seq_num

        msg_body = {
            "router_graph": self.router_graph,
            "origin": origin,
            "seq_num": seq_num
        }
        
        send = json.dumps(msg_body)
        self.send_to_neighbors(send)

        # print("this is the current graph of " + str(self.id))
        # print(self.router_graph)
        
        # for edge in self.router_graph:
        #     src, dst = edge
        #     msg_body = {
        #         "src": src,
        #         "dst": dst,
        #         "visited": [self.id],
        #         "lat": self.router_graph[(src, dst)],
        #         "time": msg["time"]
        #     }
        #     send = json.dumps(msg_body)
        #     self.send_to_neighbors(send)
        
        # msg_body = {
        #     "router_graph": self.router_graph,
        #     "visited": new_visited
        # }
        # send = json.dumps(msg_body)
        # self.send_to_neighbors(send)
        
    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        dsts, prvs = self.shortest_path()
        if destination not in dsts or dsts[destination] == float('inf'):
            # print("failure")
            return -1
        
        curr = destination
        while prvs[curr] is not self.id:
            curr = prvs[curr]
            # print("get next hop")
        return curr

    def shortest_path(self):
        dsts = {}
        prvs = {}

        # create list of vertices
        vertices = set()
        for edge in self.router_graph:
            src, dst = map(int, edge.split(","))
            vertices.add(src)
            vertices.add(dst) 
        vertices = list(vertices)

        for vertex in vertices:
            dsts[vertex] = float('inf')
            prvs[vertex] = None

        dsts[self.id] = 0

        pq = []
        heapq.heapify(pq)
        for vertex in vertices:
            heapq.heappush(pq, [dsts[vertex], vertex])
        # print(f"vertices: {vertices}")

        while pq:
            # find minimum cost vertex
            _, min_vertex = heapq.heappop(pq)

            # print(min_vertex)

            # get all neighbors of vertex
            min_neighbors = set()
            for edge in self.router_graph:
                src, dst = map(int, edge.split(","))
                if src == min_vertex:
                    min_neighbors.add(dst)
                elif dst == min_vertex:
                    min_neighbors.add(src)
            min_neighbors = list(min_neighbors)
            #print("**")
            #print(f"min neighbors: {min_neighbors}")
            
            for neighbor in min_neighbors:
                alt = dsts[min_vertex] + self.router_graph[f"{min_vertex},{neighbor}"]
                if alt < dsts[neighbor]:
                    #print("***")
                    #print(alt)
                    dsts[neighbor] = alt

                    i = 0
                    for tuple in pq:
                        _, vertex = tuple
                        if vertex == neighbor:
                            break
                        i += 1
                    pq[i][0] = alt
                    heapq.heapify(pq)

                    prvs[neighbor] = min_vertex
            
        return dsts, prvs