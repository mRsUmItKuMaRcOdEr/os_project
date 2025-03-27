import sys
import threading
import time
from collections import defaultdict
import matplotlib.pyplot as plt
import networkx as nx
from tkinter import *
from tkinter import ttk, messagebox, simpledialog

class ProcessResourceTracker:
    def __init__(self):
        self.processes = {}
        self.resources = defaultdict(list)
        self.lock = threading.Lock()
        self.running = True
        
    def start_monitoring(self):
        monitor_thread = threading.Thread(target=self._monitor_system)
        monitor_thread.daemon = True
        monitor_thread.start()
        
    def _monitor_system(self):
        while self.running:
            with self.lock:
                self._update_processes()
            time.sleep(1)
            
    def _update_processes(self):
        """Maintain process list (no automatic resource allocation)"""
        pass
    
    def add_process(self, pid, name):
        with self.lock:
            self.processes[pid] = {
                'name': name,
                'status': 'running',
                'resources': [],
                'waiting_for': None
            }
    
    def allocate_resource(self, pid, resource):
        with self.lock:
            if pid in self.processes:
                self.resources[resource].append(pid)
                self.processes[pid]['resources'].append(resource)
                return True
            return False
    
    def set_waiting_for(self, pid, resource):
        with self.lock:
            if pid in self.processes:
                self.processes[pid]['waiting_for'] = resource
                return True
            return False
    
    def get_system_state(self):
        with self.lock:
            return {
                'processes': self.processes.copy(),
                'resources': dict(self.resources)
            }
    
    def clear_system(self):
        with self.lock:
            self.processes.clear()
            self.resources.clear()
    
    def stop_monitoring(self):
        self.running = False


class DeadlockDetector:
    def __init__(self, tracker):
        self.tracker = tracker
        self.detection_history = []
        
    def detect_deadlocks(self):
        system_state = self.tracker.get_system_state()
        processes = system_state['processes']
        resources = system_state['resources']
        
        # Build resource allocation graph
        graph = nx.DiGraph()
        
        # Add nodes
        for pid in processes:
            graph.add_node(f"P{pid}", type='process')
        for rid in resources:
            graph.add_node(f"R{rid}", type='resource')
        
        # Add edges
        for pid, pdata in processes.items():
            # Process -> Resource (holds)
            for rid in pdata['resources']:
                graph.add_edge(f"P{pid}", f"R{rid}")
            
            # Resource -> Process (waiting for)
            if pdata['waiting_for']:
                graph.add_edge(f"R{pdata['waiting_for']}", f"P{pid}")
        
        # Detect cycles
        try:
            cycles = list(nx.simple_cycles(graph))
            deadlocks = [cycle for cycle in cycles if len(cycle) >= 4]
            
            if deadlocks:
                detection_time = time.strftime("%Y-%m-%d %H:%M:%S")
                self.detection_history.append({
                    'time': detection_time,
                    'deadlocks': deadlocks,
                    'graph': graph
                })
                return deadlocks
        except nx.NetworkXNoCycle:
            pass
        
        return None


class DeadlockResolver:
    def __init__(self, detector):
        self.detector = detector
        
    def suggest_resolutions(self, deadlock):
        resolutions = []
        processes_in_deadlock = set()
        resources_in_deadlock = set()
        
        for node in deadlock:
            if node.startswith('P'):
                processes_in_deadlock.add(int(node[1:]))
            elif node.startswith('R'):
                resources_in_deadlock.add(node[1:])
        
        if processes_in_deadlock:
            resolutions.append({
                'type': 'process_termination',
                'description': 'Terminate one process involved in the deadlock',
                'targets': list(processes_in_deadlock),
                'recommendation': f"Terminate process: {min(processes_in_deadlock)} (lowest PID)"
            })
        
        if resources_in_deadlock:
            resolutions.append({
                'type': 'resource_preemption',
                'description': 'Preempt one resource involved in the deadlock',
                'targets': list(resources_in_deadlock),
                'recommendation': f"Preempt resource: {resources_in_deadlock.pop()}"
            })
        
        return resolutions


class DeadlockDetectionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automated Deadlock Detection Tool")
        
        # Initialize components
        self.tracker = ProcessResourceTracker()
        self.detector = DeadlockDetector(self.tracker)
        self.resolver = DeadlockResolver(self.detector)
        
        # Start monitoring
        self.tracker.start_monitoring()
        
        # Setup GUI
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Main frame
        mainframe = ttk.Frame(self.root, padding="10")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Title
        ttk.Label(mainframe, text="Automated Deadlock Detection Tool", 
                 font=('Helvetica', 14, 'bold')).grid(column=1, row=1, columnspan=2, pady=10)
        
        # Input Section
        ttk.Label(mainframe, text="Create Deadlock Scenario:", font=('Helvetica', 11, 'bold')).grid(column=1, row=2, columnspan=2, sticky=W, pady=5)
        
        ttk.Button(mainframe, text="Add Process", command=self.add_process_dialog).grid(column=1, row=3, pady=5)
        ttk.Button(mainframe, text="Allocate Resource", command=self.allocate_resource_dialog).grid(column=2, row=3, pady=5)
        ttk.Button(mainframe, text="Set Waiting For", command=self.set_waiting_dialog).grid(column=1, row=4, pady=5)
        ttk.Button(mainframe, text="Clear System", command=self.clear_system).grid(column=2, row=4, pady=5)
        
        # Detection Section
        ttk.Label(mainframe, text="Deadlock Detection:", font=('Helvetica', 11, 'bold')).grid(column=1, row=5, columnspan=2, sticky=W, pady=5)
        
        ttk.Button(mainframe, text="Check for Deadlocks", command=self.check_for_deadlocks).grid(column=1, row=6, pady=5)
        ttk.Button(mainframe, text="Visualize System", command=self.visualize_system).grid(column=2, row=6, pady=5)
        
        # Results area
        self.results_text = Text(mainframe, width=70, height=15, wrap=WORD, state=DISABLED)
        self.results_text.grid(column=1, row=7, columnspan=2, pady=10)
        
        # Status bar
        self.status_var = StringVar(value="Ready")
        ttk.Label(mainframe, textvariable=self.status_var).grid(column=1, row=8, columnspan=2, sticky=W)
        
    def add_process_dialog(self):
        pid = simpledialog.askinteger("Add Process", "Enter Process ID (PID):")
        if pid is not None:
            name = simpledialog.askstring("Add Process", "Enter Process Name:")
            if name:
                self.tracker.add_process(pid, name)
                self.log_message(f"Added process: PID={pid}, Name='{name}'")
    
    def allocate_resource_dialog(self):
        pid = simpledialog.askinteger("Allocate Resource", "Enter Process ID (PID):")
        if pid is not None:
            resource = simpledialog.askstring("Allocate Resource", "Enter Resource ID:")
            if resource:
                if self.tracker.allocate_resource(pid, resource):
                    self.log_message(f"Allocated resource '{resource}' to process {pid}")
                else:
                    messagebox.showerror("Error", f"Process {pid} not found!")
    
    def set_waiting_dialog(self):
        pid = simpledialog.askinteger("Set Waiting For", "Enter Process ID (PID):")
        if pid is not None:
            resource = simpledialog.askstring("Set Waiting For", "Enter Resource ID this process is waiting for:")
            if resource:
                if self.tracker.set_waiting_for(pid, resource):
                    self.log_message(f"Set process {pid} to wait for resource '{resource}'")
                else:
                    messagebox.showerror("Error", f"Process {pid} not found!")
    
    def clear_system(self):
        self.tracker.clear_system()
        self.log_message("System cleared - all processes and resources removed")
    
    def check_for_deadlocks(self):
        deadlocks = self.detector.detect_deadlocks()
        self.results_text.config(state=NORMAL)
        self.results_text.delete(1.0, END)
        
        if deadlocks:
            self.status_var.set("Deadlock detected!")
            self.results_text.insert(END, f"DEADLOCK DETECTED at {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for i, deadlock in enumerate(deadlocks, 1):
                self.results_text.insert(END, f"Deadlock #{i}:\n")
                self.results_text.insert(END, " → ".join(deadlock) + " → ...\n\n")
                
                # Show resolution options
                resolutions = self.resolver.suggest_resolutions(deadlock)
                self.results_text.insert(END, "Possible resolutions:\n")
                for res in resolutions:
                    self.results_text.insert(END, f"- {res['recommendation']}\n")
                
                self.results_text.insert(END, "\n")
        else:
            self.status_var.set("No deadlock detected")
            self.results_text.insert(END, "No deadlock detected in current system state.\n")
            self.results_text.insert(END, "Create a circular wait to test deadlock detection.\n\n")
            self.results_text.insert(END, "Example deadlock scenario:\n")
            self.results_text.insert(END, "1. Process 1 holds Resource A\n")
            self.results_text.insert(END, "2. Process 2 holds Resource B\n")
            self.results_text.insert(END, "3. Process 1 waits for Resource B\n")
            self.results_text.insert(END, "4. Process 2 waits for Resource A\n")
        
        self.results_text.config(state=DISABLED)
    
    def visualize_system(self):
        system_state = self.tracker.get_system_state()
        processes = system_state['processes']
        resources = system_state['resources']
        
        graph = nx.DiGraph()
        
        # Add nodes
        for pid in processes:
            graph.add_node(f"P{pid}", type='process', label=f"Process {pid}")
        for rid in resources:
            graph.add_node(f"R{rid}", type='resource', label=f"Resource {rid}")
        
        # Add edges
        for pid, pdata in processes.items():
            # Process -> Resource (holds)
            for rid in pdata['resources']:
                graph.add_edge(f"P{pid}", f"R{rid}", label='holds')
            
            # Resource -> Process (waiting for)
            if pdata['waiting_for']:
                graph.add_edge(f"R{pdata['waiting_for']}", f"P{pid}", label='waits for')
        
        # Draw the graph
        plt.figure(figsize=(10, 8))
        
        pos = nx.spring_layout(graph)
        node_colors = ['lightblue' if graph.nodes[node]['type'] == 'process' else 'lightgreen' for node in graph.nodes()]
        
        nx.draw(graph, pos, with_labels=True, 
               labels={node: graph.nodes[node]['label'] for node in graph.nodes()},
               node_color=node_colors, node_size=2500, 
               font_size=10, font_weight='bold')
        
        # Draw edge labels
        edge_labels = nx.get_edge_attributes(graph, 'label')
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)
        
        plt.title("Current System State - Resource Allocation Graph")
        plt.show()
    
    def log_message(self, message):
        self.results_text.config(state=NORMAL)
        self.results_text.insert(END, f"{message}\n")
        self.results_text.see(END)
        self.results_text.config(state=DISABLED)
        self.status_var.set(message)


def main():
    root = Tk()
    app = DeadlockDetectionGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

    #this is very good project