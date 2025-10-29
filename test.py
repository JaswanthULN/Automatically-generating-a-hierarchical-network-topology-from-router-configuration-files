import tkinter as tk
import time
import threading
import queue  # Used for BFS pathfinding

# A dictionary to store the (x, y) coordinates of our devices
NODE_COORDINATES = {
    "PC0": (50, 250),
    "Switch0": (150, 250),
    "R1": (250, 150),
    "R2": (400, 350),
    "R3": (550, 150),
    "Switch1": (650, 250),
    "PC1": (750, 200),
    "Server0": (750, 300)
}

# Adjacency list representing the network graph (all links)
NETWORK_GRAPH = {
    "PC0": ["Switch0"],
    "Switch0": ["PC0", "R1"],
    "R1": ["Switch0", "R3", "R2"],
    "R2": ["R1", "R3"],
    "R3": ["R1", "R2", "Switch1"],
    "Switch1": ["R3", "PC1", "Server0"],
    "PC1": ["Switch1"],
    "Server0": ["Switch1"]
}


class NetworkSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic Network Visual Simulator")

        # Create canvas
        self.canvas = tk.Canvas(root, width=800, height=500, bg="white")
        self.canvas.pack()

        # --- Control Frame ---
        self.control_frame = tk.Frame(root)
        self.control_frame.pack()

        node_list = list(NODE_COORDINATES.keys())

        tk.Label(self.control_frame, text="From:").pack(side=tk.LEFT, padx=(10, 2))
        self.source_var = tk.StringVar(root)
        self.source_var.set(node_list[0])
        self.source_menu = tk.OptionMenu(self.control_frame, self.source_var, *node_list)
        self.source_menu.pack(side=tk.LEFT)

        tk.Label(self.control_frame, text="To:").pack(side=tk.LEFT, padx=(10, 2))
        self.dest_var = tk.StringVar(root)
        self.dest_var.set(node_list[-1])
        self.dest_menu = tk.OptionMenu(self.control_frame, self.dest_var, *node_list)
        self.dest_menu.pack(side=tk.LEFT, padx=(0, 10))

        self.ping_button = tk.Button(self.control_frame,
                                     text="Start Simulation",
                                     command=self.start_simulation_thread)
        self.ping_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.status_label = tk.Label(self.control_frame, text="Status: Ready", fg="blue")
        self.status_label.pack(side=tk.LEFT)

        # Draw the topology
        self.draw_topology()

    def draw_topology(self):
        """Draw all network devices and links."""
        # Main links
        self.canvas.create_line(NODE_COORDINATES["PC0"], NODE_COORDINATES["Switch0"], fill="black", width=2)
        self.canvas.create_line(NODE_COORDINATES["Switch0"], NODE_COORDINATES["R1"], fill="black", width=2)
        self.canvas.create_line(NODE_COORDINATES["R1"], NODE_COORDINATES["R3"], fill="black", width=2, dash=(6, 2))
        self.canvas.create_line(NODE_COORDINATES["R3"], NODE_COORDINATES["Switch1"], fill="black", width=2)
        self.canvas.create_line(NODE_COORDINATES["Switch1"], NODE_COORDINATES["PC1"], fill="black", width=2)
        self.canvas.create_line(NODE_COORDINATES["Switch1"], NODE_COORDINATES["Server0"], fill="black", width=2)

        # Backup (gray dashed)
        self.canvas.create_line(NODE_COORDINATES["R1"], NODE_COORDINATES["R2"], fill="gray", width=2, dash=(4, 4))
        self.canvas.create_line(NODE_COORDINATES["R2"], NODE_COORDINATES["R3"], fill="gray", width=2, dash=(4, 4))

        # Draw nodes
        for name, (x, y) in NODE_COORDINATES.items():
            if "R" in name:
                self.canvas.create_oval(x - 15, y - 15, x + 15, y + 15, fill="lightblue", outline="black", width=2)
            else:
                self.canvas.create_rectangle(x - 20, y - 15, x + 20, y + 15, fill="lightgray", outline="black", width=2)
            self.canvas.create_text(x, y + 25, text=name, font=("Arial", 9, "bold"))

    def find_shortest_path(self, start_node, end_node):
        """Find the shortest path between nodes using BFS."""
        visited = set()
        q = queue.Queue()
        q.put((start_node, [start_node]))
        visited.add(start_node)

        while not q.empty():
            current_node, path = q.get()
            if current_node == end_node:
                return path
            for neighbor in NETWORK_GRAPH.get(current_node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    q.put((neighbor, new_path))
        return None

    def start_simulation_thread(self):
        """Start the animation in a new thread."""
        source = self.source_var.get()
        dest = self.dest_var.get()

        if source == dest:
            self.status_label.config(text="Status: Source and Destination are the same.", fg="red")
            return

        path_nodes = self.find_shortest_path(source, dest)
        if path_nodes is None:
            self.status_label.config(text=f"Status: No path from {source} to {dest}.", fg="red")
            return

        sim_thread = threading.Thread(target=self.animate_ping, args=(path_nodes,), daemon=True)
        sim_thread.start()

    def move_packet(self, start, end, color):
        """Animate a packet between two coordinates."""
        x1, y1 = start
        x2, y2 = end
        packet = self.canvas.create_oval(x1 - 5, y1 - 5, x1 + 5, y1 + 5, fill=color, outline=color)
        steps = 25
        dx = (x2 - x1) / steps
        dy = (y2 - y1) / steps
        for _ in range(steps):
            self.canvas.move(packet, dx, dy)
            self.root.update()
            time.sleep(0.03)
        self.canvas.delete(packet)

    def animate_ping(self, path_nodes):
        """Animate ping request and reply across the path."""
        self.ping_button.config(state=tk.DISABLED)
        self.source_menu.config(state=tk.DISABLED)
        self.dest_menu.config(state=tk.DISABLED)
        self.status_label.config(text=f"Status: Sending Request {path_nodes[0]} → {path_nodes[-1]}", fg="orange")

        # Request path
        for i in range(len(path_nodes) - 1):
            start, end = NODE_COORDINATES[path_nodes[i]], NODE_COORDINATES[path_nodes[i + 1]]
            self.move_packet(start, end, "green")

        time.sleep(0.5)
        self.status_label.config(text=f"Status: Sending Reply {path_nodes[-1]} → {path_nodes[0]}", fg="green")

        # Reply path (reverse)
        for i in range(len(path_nodes) - 1, 0, -1):
            start, end = NODE_COORDINATES[path_nodes[i]], NODE_COORDINATES[path_nodes[i - 1]]
            self.move_packet(start, end, "blue")

        self.status_label.config(text="Status: Ping Complete!", fg="blue")

        # Re-enable controls
        self.ping_button.config(state=tk.NORMAL)
        self.source_menu.config(state=tk.NORMAL)
        self.dest_menu.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkSimulator(root)
    root.mainloop()
