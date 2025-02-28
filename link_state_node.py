from simulator.node import Node, Link
import json
import heapq

class Link_State_Node(Node):

    def __init__(self, id):
        super().__init__(id)
        self.router_graph = {} # adj matrix - key: (src, dst) -> val: cost
        self.node_messages = {} # key: node id, val: seq num
        self.adj_list = {} # key: node (int), val: list of nodes (ints)
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
            if neighbor in self.neighbors:
                self.neighbors.remove(neighbor)

            self.router_graph.pop(f"{self.id},{neighbor}", None)
            self.router_graph.pop(f"{neighbor},{self.id}", None)

            msg_body = {
                "router_graph": self.router_graph,
                "origin": self.id,
                "seq_num": self.seq_num,
                "deleted_link": f"{self.id},{neighbor}"
            }

            self.seq_num += 1
            msg_to_send = json.dumps(msg_body)
            self.send_to_neighbors(msg_to_send)
            return
        
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)

        self.router_graph[f"{self.id},{neighbor}"] = latency
        self.router_graph[f"{neighbor},{self.id}"] = latency

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
        routing_table = msg["router_graph"]
        origin = msg["origin"]
        seq_num = msg["seq_num"]

        if origin in self.node_messages and seq_num <= self.node_messages[origin]:
            return
        self.node_messages[origin] = seq_num

        if "deleted_link" in msg:
            edge = msg["deleted_link"]
            src, dst = map(int, edge.split(","))
            if f"{src},{dst}" in self.router_graph and f"{dst},{src}" in self.router_graph:
                del self.router_graph[f"{src},{dst}"]
                del self.router_graph[f"{dst},{src}"]

            msg_body = {
                "router_graph": self.router_graph,
                "origin": origin,
                "seq_num": seq_num,
                "deleted_link": edge
            }
            send = json.dumps(msg_body)
            self.send_to_neighbors(send)
            return

        prev_graph_state = self.router_graph.copy()
        self.router_graph.update(routing_table)

        if prev_graph_state != self.router_graph and origin != self.id:
            msg_body = {
                "router_graph": self.router_graph,
                "origin": origin,
                "seq_num": seq_num
            }
            
            send = json.dumps(msg_body)
            self.send_to_neighbors(send)
        
    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        dsts, prvs = self.shortest_path()
        if destination not in dsts or dsts[destination] == float('inf'):
            return -1
        
        curr = destination
        while prvs[curr] != self.id:
            curr = prvs[curr]
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

        for vertex in vertices:
            dsts[vertex] = float('inf')
            prvs[vertex] = None

        dsts[self.id] = 0

        pq = []
        heapq.heapify(pq)
        for vertex in vertices:
            heapq.heappush(pq, [dsts[vertex], vertex])

        while pq:
            # find minimum cost vertex
            _, min_vertex = heapq.heappop(pq)

            # get all neighbors of vertex
            min_neighbors = set()
            for edge in self.router_graph:
                src, dst = map(int, edge.split(","))
                if src == min_vertex:
                    min_neighbors.add(dst)
                elif dst == min_vertex:
                    min_neighbors.add(src)
            
            for neighbor in min_neighbors:
                alt = dsts[min_vertex] + self.router_graph[f"{min_vertex},{neighbor}"]
                if alt < dsts[neighbor]:
                    dsts[neighbor] = alt

                    # i = 0
                    # for tuple in pq:
                    #     _, vertex = tuple
                    #     if vertex == neighbor:
                    #         break
                    #     i += 1
                    # pq[i][0] = alt
                    # heapq.heapify(pq)
                    for i in range(len(pq)):
                        if pq[i][1] == neighbor:
                            pq[i][0] = alt
                            break
                    heapq.heapify(pq)


                    prvs[neighbor] = min_vertex
            
        return dsts, prvs
