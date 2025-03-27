import networkx as nx
import matplotlib.pyplot as plt

# Module 1: Input and Simulation
def get_system_state():
    # Sample input: Process P1 holds R1, requests R2; P2 holds R2, requests R1
    allocation = {  # Current allocation (who holds what)
        "P1": "R1",
        "P2": "R2"
    }
    request = {     # Current requests (who wants what)
        "P1": "R2",
        "P2": "R1"
    }
    return allocation, request

# Module 2: Deadlock Detection
def detect_deadlock(allocation, request):
    G = nx.DiGraph()  # Directed graph for resource allocation
    
    # Add edges: Process -> Resource (request), Resource -> Process (allocation)
    for proc, res in allocation.items():
        G.add_edge(res, proc)  # Resource held by process
    for proc, res in request.items():
        G.add_edge(proc, res)  # Process requests resource
    
    # Detect cycles
    try:
        cycles = list(nx.find_cycle(G, orientation="original"))
        return True, cycles
    except nx.NetworkXNoCycle:
        return False, []

# Module 3: Visualization and Resolution
def visualize_and_resolve(G, deadlock_detected, cycles):
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=1500, font_size=10, arrows=True)
    
    if deadlock_detected:
        # Highlight cycle edges
        cycle_edges = [(u, v) for u, v, _ in cycles]
        nx.draw_networkx_edges(G, pos, edgelist=cycle_edges, edge_color="red", width=2)
        plt.title("Deadlock Detected!")
        
        # Suggest resolution
        print("Deadlock detected with cycle:", cycles)
        print("Resolution Suggestion: Preempt a resource (e.g., R1 from P2) or terminate a process (e.g., P1).")
    else:
        plt.title("No Deadlock Detected")
    
    plt.show()

# Main execution
def main():
    # Simulate system state
    allocation, request = get_system_state()
    
    # Build graph and detect deadlock
    G = nx.DiGraph()
    for proc, res in allocation.items():
        G.add_edge(res, proc)
    for proc, res in request.items():
        G.add_edge(proc, res)
    
    deadlock_detected, cycles = detect_deadlock(allocation, request)
    
    # Visualize and suggest resolution
    visualize_and_resolve(G, deadlock_detected, cycles)

if __name__ == "__main__":
    main()

    # hii my nszmse is sumit