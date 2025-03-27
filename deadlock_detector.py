import sys
import threading
import time
from collections import defaultdict
import psutil
import matplotlib.pyplot as plt
import networkx as nx
from tkinter import *
from tkinter import ttk, messagebox

class ProcessResourceTracker:
    def __init__(self):
        self.processes = {}
        self.resources = defaultdict(list)
        self.lock = threading.Lock()
        self.running = True
        
    def start_monitoring(self):
        """Start monitoring processes and resources in a separate thread"""
        monitor_thread = threading.Thread(target=self._monitor_system)
        monitor_thread.daemon = True
        monitor_thread.start()
        
    def _monitor_system(self):
        """Continuously monitor system processes and resources"""
        while self.running:
            with self.lock:
                self._update_processes()
                self._update_resources()
            time.sleep(1)  # Update interval
            
    def _update_processes(self):
        """Update information about running processes"""
        self.processes.clear()
        for proc in psutil.process_iter(['pid', 'name', 'status']):
            try:
                self.processes[proc.info['pid']] = {
                    'name': proc.info['name'],
                    'status': proc.info['status'],
                    'resources': []
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
    def _update_resources(self):
        """Simulate resource allocation (in a real system, this would track actual resources)"""
        self.resources.clear()
        # Simulate some resource allocations
        if self.processes:
            pids = list(self.processes.keys())
            for i, pid in enumerate(pids):
                resource_id = f"R{i%5}"  # 5 simulated resources
                self.resources[resource_id].append(pid)
                self.processes[pid]['resources'].append(resource_id)
    
    def get_system_state(self):
        """Get current system state snapshot"""
        with self.lock:
            return {
                'processes': self.processes.copy(),
                'resources': dict(self.resources)
            }
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False


class DeadlockDetector:
    def __init__(self, tracker):
        self.tracker = tracker
        self.detection_history = []
        
    def detect_deadlocks(self):
        """Detect deadlocks using Resource Allocation Graph (RAG) approach"""
        system_state = self.tracker.get_system_state()
        processes = system_state['processes']
        resources = system_state['resources']
        
        # Build the resource allocation graph
        graph = nx.DiGraph()
        
        # Add nodes (processes and resources)
        for pid in processes:
            graph.add_node(f"P{pid}", type='process')
            
        for rid in resources:
            graph.add_node(f"R{rid}", type='resource')
        
        # Add edges (process -> resource and resource -> process)
        for pid, pdata in processes.items():
            for rid in pdata['resources']:
                graph.add_edge(f"P{pid}", f"R{rid}")  # Process holds resource
                
        for rid, pids in resources.items():
            for pid in pids:
                graph.add_edge(f"R{rid}", f"P{pid}")  # Process is waiting for resource
        
        # Detect cycles in the graph (indicate deadlocks)
        try:
            cycles = list(nx.simple_cycles(graph))
            deadlocks = []
            
            for cycle in cycles:
                if len(cycle) >= 4:  # At least two processes and two resources for a deadlock
                    deadlocks.append(cycle)
            
            if deadlocks:
                detection_time = time.strftime("%Y-%m-%d %H:%M:%S")
                detection_entry = {
                    'time': detection_time,
                    'deadlocks': deadlocks,
                    'graph': graph
                }
                self.detection_history.append(detection_entry)
                return deadlocks
                
        except nx.NetworkXNoCycle:
            pass
            
        return None
    
    def get_detection_history(self):
        """Get history of all detected deadlocks"""
        return self.detection_history


class DeadlockResolver:
    def __init__(self, detector):
        self.detector = detector
        
    def suggest_resolutions(self, deadlock):
        """Suggest possible resolutions for a detected deadlock"""
        resolutions = []
        
        # Strategy 1: Process termination
        processes_in_deadlock = set()
        for node in deadlock:
            if node.startswith('P'):
                pid = int(node[1:])
                processes_in_deadlock.add(pid)
                
        if processes_in_deadlock:
            resolutions.append({
                'type': 'process_termination',
                'description': 'Terminate one of the processes involved in the deadlock',
                'processes': list(processes_in_deadlock),
                'recommendation': f"Terminate process with PID: {min(processes_in_deadlock)} (oldest)"
            })
        
        # Strategy 2: Resource preemption
        resources_in_deadlock = set()
        for node in deadlock:
            if node.startswith('R'):
                resources_in_deadlock.add(node[1:])
                
        if resources_in_deadlock:
            resolutions.append({
                'type': 'resource_preemption',
                'description': 'Preempt one of the resources involved in the deadlock',
                'resources': list(resources_in_deadlock),
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
        
        # Start periodic deadlock detection
        self.detect_deadlocks_periodically()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Main frame
        mainframe = ttk.Frame(self.root, padding="10")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Title
        ttk.Label(mainframe, text="Automated Deadlock Detection Tool", 
                 font=('Helvetica', 14, 'bold')).grid(column=1, row=1, pady=10)
        
        # System status
        ttk.Label(mainframe, text="System Status:").grid(column=1, row=2, sticky=W)
        self.status_var = StringVar(value="Monitoring system...")
        ttk.Label(mainframe, textvariable=self.status_var).grid(column=2, row=2, sticky=W)
        
        # Detection button
        ttk.Button(mainframe, text="Check for Deadlocks Now", 
                  command=self.check_for_deadlocks).grid(column=1, row=3, pady=10)
        
        # Results area
        ttk.Label(mainframe, text="Detection Results:").grid(column=1, row=4, sticky=W, pady=5)
        self.results_text = Text(mainframe, width=60, height=10, wrap=WORD)
        self.results_text.grid(column=1, row=5, columnspan=2)
        
        # Visualization button
        ttk.Button(mainframe, text="Visualize Last Detection", 
                  command=self.visualize_last_detection).grid(column=1, row=6, pady=10)
        
        # Resolution button
        ttk.Button(mainframe, text="Show Resolution Options", 
                  command=self.show_resolution_options).grid(column=2, row=6, pady=10)
        
        # History button
        ttk.Button(mainframe, text="View Detection History", 
                  command=self.view_detection_history).grid(column=1, row=7, pady=10)
        
        # Exit button
        ttk.Button(mainframe, text="Exit", 
                  command=self.cleanup_and_exit).grid(column=2, row=7, pady=10)
    
    def detect_deadlocks_periodically(self):
        """Periodically check for deadlocks"""
        deadlocks = self.detector.detect_deadlocks()
        if deadlocks:
            self.status_var.set("Deadlock detected!")
            self.display_deadlock_info(deadlocks)
        else:
            self.status_var.set("No deadlocks detected")
        
        # Schedule next detection
        self.root.after(5000, self.detect_deadlocks_periodically)
    
    def check_for_deadlocks(self):
        """Manual check for deadlocks"""
        deadlocks = self.detector.detect_deadlocks()
        if deadlocks:
            self.status_var.set("Deadlock detected!")
            self.display_deadlock_info(deadlocks)
            messagebox.showwarning("Deadlock Detected", "A deadlock has been detected in the system!")
        else:
            self.status_var.set("No deadlocks detected")
            messagebox.showinfo("No Deadlock", "No deadlocks detected in the system.")
    
    def display_deadlock_info(self, deadlocks):
        """Display information about detected deadlocks"""
        self.results_text.delete(1.0, END)
        self.results_text.insert(END, f"Deadlock detected at {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for i, deadlock in enumerate(deadlocks, 1):
            self.results_text.insert(END, f"Deadlock #{i}:\n")
            self.results_text.insert(END, " → ".join(deadlock) + " → ...\n\n")
    
    def visualize_last_detection(self):
        """Visualize the last detected deadlock"""
        history = self.detector.get_detection_history()
        if not history:
            messagebox.showinfo("No History", "No deadlocks detected yet.")
            return
            
        last_detection = history[-1]
        graph = last_detection['graph']
        
        plt.figure(figsize=(10, 8))
        
        # Color nodes based on type
        node_colors = []
        for node in graph.nodes():
            if node.startswith('P'):
                node_colors.append('lightblue')
            else:
                node_colors.append('lightgreen')
        
        # Draw the graph
        pos = nx.spring_layout(graph)
        nx.draw(graph, pos, with_labels=True, node_color=node_colors, 
               node_size=2000, font_size=10, font_weight='bold')
        
        plt.title("Resource Allocation Graph with Deadlock")
        plt.show()
    
    def show_resolution_options(self):
        """Show resolution options for the last detected deadlock"""
        history = self.detector.get_detection_history()
        if not history:
            messagebox.showinfo("No Deadlock", "No deadlocks detected yet.")
            return
            
        last_deadlock = history[-1]['deadlocks'][0]  # Get first deadlock in last detection
        resolutions = self.resolver.suggest_resolutions(last_deadlock)
        
        resolution_window = Toplevel(self.root)
        resolution_window.title("Deadlock Resolution Options")
        
        ttk.Label(resolution_window, text="Suggested Resolution Strategies:", 
                 font=('Helvetica', 11, 'bold')).pack(pady=10)
        
        for i, resolution in enumerate(resolutions, 1):
            frame = ttk.Frame(resolution_window, padding=10)
            frame.pack(fill=X, padx=5, pady=5)
            
            ttk.Label(frame, text=f"Option {i}: {resolution['type'].replace('_', ' ').title()}",
                     font=('Helvetica', 10, 'bold')).pack(anchor=W)
            ttk.Label(frame, text=resolution['description'], wraplength=400).pack(anchor=W)
            
            if 'processes' in resolution:
                ttk.Label(frame, text=f"Involved Processes: {', '.join(map(str, resolution['processes']))}").pack(anchor=W)
            if 'resources' in resolution:
                ttk.Label(frame, text=f"Involved Resources: {', '.join(resolution['resources'])}").pack(anchor=W)
            
            ttk.Label(frame, text=f"Recommendation: {resolution['recommendation']}",
                     font=('Helvetica', 9, 'italic')).pack(anchor=W, pady=(5, 0))
    
    def view_detection_history(self):
        """Show a window with all detected deadlocks"""
        history = self.detector.get_detection_history()
        if not history:
            messagebox.showinfo("No History", "No deadlocks detected yet.")
            return
            
        history_window = Toplevel(self.root)
        history_window.title("Deadlock Detection History")
        
        tree = ttk.Treeview(history_window, columns=('Time', 'Deadlocks'), show='headings')
        tree.heading('Time', text='Detection Time')
        tree.heading('Deadlocks', text='Deadlocks Detected')
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        for entry in history:
            deadlock_count = len(entry['deadlocks'])
            tree.insert('', 'end', values=(entry['time'], f"{deadlock_count} deadlock(s)"))
    
    def cleanup_and_exit(self):
        """Clean up resources and exit"""
        self.tracker.stop_monitoring()
        self.root.destroy()


def main():
    root = Tk()
    app = DeadlockDetectionGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

    #this is good project