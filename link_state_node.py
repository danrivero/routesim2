from simulator.node import Node, Link
import json
import heapq

class Link_State_Node(Node):

    def __init__(self, id):
        super().__init__(id)
        self.router_graph = {} # adj matrix - key: (src, dst) -> val: cost
        self.node_messages = {} # key: node id, value: seq_num of last received message
        self.seq_num = 0 # ensures uniqueness 

    # Return a string
    def __str__(self):
        output = "Node " + str(self.id) + ": " + str(self.neighbors) + ", " + str(self.router_graph)
        return output

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        if latency == -1:
            cond_lat = float('inf')
        else:
            cond_lat = latency
        # when link is updated, propagate new self information to neighbors
        # json message includes <source, destination, sequence number, and latency>
        msg_body = {
            "src": self.id,
            "dst": neighbor,
            "seq_num": self.seq_num,
            "lat": cond_lat
        }
        msg_to_send = json.dumps(msg_body)
        self.seq_num += 1
        self.send_to_neighbors(msg_to_send)

    # Fill in this function
    def process_incoming_routing_message(self, m):
        # when receiving updated info, forward it to all neighbors
        msg = json.load(m)
        if not self.node_messages[msg["src"]] or self.node_messages[msg["src"]] <= msg["seq_num"]:
            self.node_messages[msg["src"]] = msg["seq_num"]

            self.router_graph[(msg["src"], msg["dst"])] = msg["lat"]
            self.router_graph[(msg["dst"], msg["src"])] = msg["lat"]

            self.send_to_neighbors(m)
        

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        return -1

    def shortest_path(self, src):
        dsts = {}
        prvs = {}

        pq = []
        
        for node in self.router_graph:
            dsts[node] = float('inf')
            heapq.heappush(pq, (float('inf'), node))
            prvs[node] = None

        dsts[self.id] = 0

        while pq:
            _, node = heapq.heappop(pq)
            for neighbor in self.neighbors:
                alt = dsts[node] + self.router_graph[node][neighbor]
                if alt < dsts[neighbor]:
                    dsts[neighbor] = alt
                    prvs[neighbor] = node
            
        return dsts, prvs
        

# 
#
#
#
#
'''def shortest_path(src, vertices, edges):
    dist = []
    prev = []
    Q = []
    for vertex in vertices:
        dist[vertex] = float('inf')
        heapq.heappush(Q, (float('inf'), vertex))
        prev[vertex] = None
    dist[src] = 0

    while Q:
        u = heapq.heappop(Q)
        Q.remove(u)
        for neighbor in u:
            ######alt = dist[u] + edge cost (latency of Link class in node.py)
            if alt < dist[neighbor]:
                dist[neighbor] = alt
                prev[neighbor] = u

    return dist, prev'''


# resp_body = {
#             "operation": "product",
#             "operands": ops,
#             "result": res
#         }

#         resp_json = json.dumps(resp_body)
#         resp = (
#             "HTTP/1.1 200 OK\r\n"
#             "Content-Type: application/json\r\n"
#             f"Content-Length: {len(resp_json)}\r\n"
#             "\r\n"
#             f"{resp_json}"
#         )