import networkx as nx

graph = nx.Graph()

graph.add_edge(1, 2)
graph.add_edge(2, 3)
print(graph.adj)
print(graph[1][2])
for n in graph:
    print(n)
