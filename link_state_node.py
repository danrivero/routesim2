from simulator.node import Node, Link
import json
import heapq

class Link_State_Node(Node):

    def __init__(self, id):
        super().__init__(id)
        self.router_graph = {} # adj matrix - key: (src, dst) -> val: cost

    # Return a string
    def __str__(self):
        output = "Node " + str(self.id) + ": " + str(self.neighbors) + ", " + str(self.router_graph)
        return output

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        if latency == -1:
            self.neighbors.remove(neighbor)
            cond_lat = float('inf')
        else:
            self.neighbors.append(neighbor)
            cond_lat = latency
        # when link is updated, propagate new self information to neighbors
        # json message includes <origin, source, destination, sequence number, and latency>
        msg_body = {
            "src": self.id,
            "dst": neighbor,
            "visited": [self.id],
            "lat": cond_lat
        }
        self.router_graph[(self.id, neighbor)] = cond_lat
        self.router_graph[(neighbor, self.id)] = cond_lat

        #print("this is the current graph of " + str(self.id))
        #print(self.router_graph)
        
        msg_to_send = json.dumps(msg_body)
        self.send_to_neighbors(msg_to_send)

    # Fill in this function
    def process_incoming_routing_message(self, m):
        # when receiving updated info, forward it to all neighbors
        msg = json.loads(m)
        # print(str(self.id) + " received a message from " + str(msg["origin"]))
        
    
        new_visited = msg["visited"].copy()
        new_visited.append(self.id)
            
        msg_body = {
            "src": msg["src"],
            "dst": msg["dst"],
            "visited": new_visited,
            "lat": msg["lat"]
        }
            
        self.router_graph[(msg["src"], msg["dst"])] = msg["lat"]
        self.router_graph[(msg["dst"], msg["src"])] = msg["lat"]

        # print("this is the current graph of " + str(self.id))
        # print(self.router_graph)
        
        send = json.dumps(msg_body)
        if self.id not in msg["visited"]:
            self.send_to_neighbors(send)
        

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        dsts, prvs = self.shortest_path()
        print(dsts)
        print(prvs)
        if destination not in dsts or dsts[destination] == float('inf'):
            print("failure")
            return -1
        
        curr = destination
        while prvs[curr] is not self.id:
            curr = prvs[curr]
        return curr

    def shortest_path(self):
        dsts = {}
        prvs = {}

        # create list of vertices
        vertices = set()
        for src, dst in self.router_graph:
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

        while pq:
            # find minimum cost vertex
            _, min_vertex = heapq.heappop(pq)

            # get all neighbors of vertex
            min_neighbors = set()
            for src, dst in self.router_graph:
                if src == min_vertex:
                    min_neighbors.add(dst)
                elif dst == min_vertex:
                    min_neighbors.add(src)
            min_neighbors = list(min_neighbors)
            #print("**")
            #print(min_neighbors)
            
            for neighbor in min_neighbors:
                alt = dsts[min_vertex] + self.router_graph[(min_vertex, neighbor)]
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