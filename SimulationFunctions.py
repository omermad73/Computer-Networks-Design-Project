import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from Host import Host
from Host2 import Host2
from Event import Event


class SimulationFunctions():


    @staticmethod
    def random_seed(seed=42):
        np.random.seed(seed)

    @staticmethod
    def generate_times(host_id, timeline, number_of_packets=2000, lambda_param=0.5):
        # generate the times between the L2 Messages
        # number_of_packets - Set the number of packets
        # lambda_param - Set the Input rate parameter for the exponential distributions
        # Generate realizations
        inter_arrival_times = np.random.exponential(scale=1 / lambda_param, size=number_of_packets)  # step 1

        # Calculate the input timeline
        arrival_times = np.cumsum(inter_arrival_times)  # step 2
        for time in arrival_times:  # step 3
            event = Event(time, "create a message", host_id)
            timeline.add_event(event)

    @staticmethod
    def dest_pool(all_host2, dest_pool):
        for host2 in all_host2:
           host2.dst_rnd_set = dest_pool
        return None

    @staticmethod
    def find_host(all_host, id):
        for host in all_host:
            if host.id == id:
                return host
        print("there is not such host")
        return None

    @staticmethod
    def find_link(links, id):
        for link in links:
            if link.id == id:
                return link
        print("there is not such link")
        return None

    @staticmethod
    def find_object(all_components, id):
        for component in all_components:
            if component.id == id:
                return component
        print("there is not such host or switch")
        return None

    @staticmethod
    def find_l2message(all_l2message, id):
        for l2message in all_l2message:
            if l2message.id == id:
                return l2message
        print("there is not such host")
        return None

    @staticmethod
    def simulation():
        pass

    @staticmethod
    def create_hosts(starting_index, num_hosts):
        hosts = []
        for i in range(starting_index + 1, starting_index + num_hosts + 1):
            mac_address = f"00:00:00:00:00:{i:02d}"  # Format the MAC address
            host = Host(mac_address)
            hosts.append(host)
        return hosts

    @staticmethod
    def create_hosts2(starting_index, num_hosts, dest_hosts=None, seed=42):
        hosts = []
        for i in range(starting_index + 1, starting_index + num_hosts + 1):
            mac_address = f"00:00:00:00:00:{i:02d}"  # Format the MAC address
            host2 = Host2(mac_address, dest_hosts, seed)
            hosts.append(host2)
        return hosts

    @staticmethod
    def draw_topology(switches, source_hosts, links, dest_hosts=None):
        G = nx.Graph()

        # Add nodes with attributes
        for switch in switches:
            G.add_node(switch.id, type='switch')
        for host in source_hosts:
            G.add_node(host.id, type='source_host')
        if dest_hosts is not None:
            for host in dest_hosts:
                G.add_node(host.id, type='dest_host')

        # Add edges
        for link in links:
            G.add_edge(link.host1.id, link.host2.id)

        # Extract positions for the nodes
        pos = nx.spring_layout(G)

        # Draw the nodes
        node_colors = []
        for node in G.nodes(data=True):
            if node[1]['type'] == 'switch':
                node_colors.append('lightblue')
            elif node[1]['type'] == 'dest_host':
                node_colors.append('red')
            else:
                node_colors.append('gray')

        nx.draw(G, pos, with_labels=True, node_size=3000, node_color=node_colors, font_size=12, font_weight='bold')
        # Add legend
        plt.text(0.02, 0.98, "Switch", horizontalalignment='left', verticalalignment='top',
                 transform=plt.gca().transAxes, bbox=dict(facecolor='lightblue', alpha=0.5))
        plt.text(0.02, 0.92, "Source Host", horizontalalignment='left', verticalalignment='top',
                 transform=plt.gca().transAxes, bbox=dict(facecolor='gray', alpha=0.5))
        plt.text(0.02, 0.86, "Dest Hosts", horizontalalignment='left', verticalalignment='top',
                 transform=plt.gca().transAxes, bbox=dict(facecolor='red', alpha=0.5))

        # Display the graph
        plt.show()
