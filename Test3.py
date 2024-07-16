import random
from Event import Event
from Host import Host
from Host2 import Host2

from Timeline import Timeline
from Link import Link
from SimulationFunctions import SimulationFunctions
from Switch import Switch
from Switch3 import SwitchLab3


class PartA:
    @staticmethod
    def main():
        # simulation settings
        number_of_packets = 10
        lambda_param = 0.5
        min_payload_size = 64
        max_payload_size = 1522
        printing_flag = 1
        terminate = 100000  # [sec] after this time the simulation is eliminated
        file_name = "macTableLog.txt"
        mac_table_log_file = open(file_name, 'w')
        mac_table_log_file = None

        #  config the random seed for the entire Topology
        seed = 9
        random.seed(seed)
        SimulationFunctions.random_seed(seed)

        # topology configuration
        different_timeline = Timeline()
        num_source_hosts = random.randint(1, 6)
        num_dest_hosts = 2
        port_num_s0 = 16

        tx_rate = 10
        propagation = 0

        # switch 2 configuration

        scheduling_discipline = "FIFO"
        #scheduling_discipline = "Priority"
        scheduling_discipline = "PGPS"

        is_fluid = False
        ttl = 10
        mac_table_size = 10
        # Creating switches
        switch = SwitchLab3(port_num_s0, mac_table_size, is_fluid, scheduling_discipline, mac_table_log_file, ttl)
        # switch1 = Switch(port_num_s1, num_hosts0 + num_hosts1 - 2, mac_table_log_file)
        # Creating hosts

        # creating dest hosts.
        dest_hosts = SimulationFunctions.create_hosts2(0, num_dest_hosts, None, seed)
        source_hosts = SimulationFunctions.create_hosts2(num_dest_hosts, num_source_hosts, None, seed)
        hosts = source_hosts + dest_hosts

        # adding dest pool
        SimulationFunctions.dest_pool(source_hosts, dest_hosts)  # updating the dest pool for every source
        # Creating links
        links = []
        switch_links = []
        for host in source_hosts:

            link = Link(host, switch, tx_rate, propagation)
            links.append(link)
            switch_links.append(link)
        for host in dest_hosts:
            link = Link(host, switch, tx_rate, propagation)
            links.append(link)
            switch_links.append(link)

        switch.connect_all_ports(switch_links)
        switches = [switch]
        all_components = hosts + switches

        # print(f"number of hosts connected to switch0: {source_hosts}")
        # print(f"number of hosts connected to switch1: {dest_hosts}")

        # start simulation
        all_l2messages = []
        should_terminate = False

        host_link_map = {}  # Create host-link map
        for link in links:
            print(link.host1)
            host_link_map[link.host1] = link
            host_link_map[link.host2] = link

        for host in source_hosts:
            SimulationFunctions.generate_times(host.id, different_timeline, number_of_packets, lambda_param)
        #  main loop
        while not should_terminate and different_timeline.events[0].scheduled_time < terminate:
            event = different_timeline.events[0]
            if event.event_type == "create a message":
                host = SimulationFunctions.find_host(hosts, event.scheduling_object_id)
                if not isinstance(host, Host):
                    raise ValueError("there is event without real host (How the hell you succeed to do it?) ")
                host.create_message(different_timeline, hosts, all_l2messages, min_payload_size, max_payload_size,
                                    printing_flag, host_link_map[host])  # adding new event
                different_timeline.done()  # remove event

            elif event.event_type == "sending a message":
                host = SimulationFunctions.find_host(hosts, event.scheduling_object_id)
                if not isinstance(host, Host):
                    raise ValueError("there is event without real host (How the hell you succeed to do it?) ")
                link = SimulationFunctions.find_link(links, host.nic)
                host.send_message(different_timeline, link, printing_flag)  # sending the list
                different_timeline.done()  # remove event

            elif event.event_type == "transmitted":
                receiver = SimulationFunctions.find_object(all_components, event.scheduling_object_id)
                if isinstance(receiver, Host):
                    link = SimulationFunctions.find_link(links, receiver.nic)
                    receiver.message_tranmitted(different_timeline, link, printing_flag)  # sending the list
                elif isinstance(receiver, SwitchLab3):
                    receiver.message_transmitted(different_timeline, event.link_id, all_l2messages, printing_flag)
                else:
                    raise ValueError("there is event without real host or switch (How the hell you succeed to do it?) ")
                different_timeline.done()  # remove event

            elif event.event_type == "message received":
                receiver = SimulationFunctions.find_object(all_components, event.next_object_id)
                l2_message = SimulationFunctions.find_l2message(all_l2messages, event.message_id)
                if not isinstance(receiver, Host) and not isinstance(receiver, Switch):
                    raise ValueError("there is event without real host or switch (How the hell you succeed to do it?) ")
                receiver.handle_message(l2_message, all_l2messages, different_timeline, event.scheduled_time,
                                        event.link_id, printing_flag)
                all_l2messages.remove(l2_message)  # remove the l2message
                different_timeline.done()  # remove event

            if not different_timeline.events:  # if there is no more events, the simulation is over
                should_terminate = True
                print("Simulation ended successfully")

        if mac_table_log_file is not None:
            mac_table_log_file.close()

        # Statistics:
        if printing_flag == 1:
            switch.print_statistics()

        # Visualization
        SimulationFunctions.draw_topology(switches, source_hosts, links,dest_hosts)


# Run the main function when the script is executed
if __name__ == "__main__":
    PartA.main()
