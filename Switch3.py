import queue
from Switch2 import SwitchLab2
from L2Message import L2Message
from Event import Event
import random
import heapq
from itertools import count


class SwitchLab3(SwitchLab2):
    def __init__(self, num_ports, mac_table_size, is_fluid=False, schedule_alg='FIFO', log_file=None,
                 seed=42, ttl=10):
        super().__init__(num_ports, mac_table_size, 'output', is_fluid, schedule_alg, log_file, seed, ttl)
        if schedule_alg != 'FIFO' and schedule_alg != 'Priority' and schedule_alg != 'PGPS':
            raise ValueError("Invalid scheduling algorithm")
        self.queues = self.configure_queues()
        # for Priority scheduling
        self.counters = [count() for _ in range(self.num_ports)]
        self.dest_ports = []

    def configure_queues(self):
        if self.schedule_alg == 'FIFO':
            return [queue.Queue() for _ in range(self.num_ports)]
        elif self.schedule_alg == 'Priority':
            return [[] for _ in range(self.num_ports)]
        else:
            return [[] for _ in range(self.num_ports)]  # TODO: change it

    def push_priority(self, queue_num: int, message: L2Message):
        heapq.heappush(self.queues[queue_num], (message.src_mac, next(self.counters[queue_num]), message))

    def pop_priority(self, queue_num, transmitted_message_id):
        if self.queues[queue_num]:
            for i, message in enumerate(self.queues[queue_num]):
                if message[2].id == transmitted_message_id:
                    del self.queues[queue_num][i]
            heapq.heapify(self.queues[queue_num])
            if not self.queues[queue_num]:
                return None
            return self.queues[queue_num][0]
        else:
            return None

    def handle_message_output(self, l2_message, all_l2messages, timeline, current_time, link_id, printing_flag):
        dst_mac = l2_message.dst_mac
        port = self.link_to_port(link_id)

        dest_port = self.find_port(dst_mac, current_time)
        if dest_port is None:
            # If the destination port is not found, flood the message, but we disable flooding in Lab 3
            # We will send the message to the next port in the list
            random_entry = random.randrange(len(self.dest_ports))
            dest_port = self.link_to_port(self.dest_ports[random_entry])

        if self.ports[dest_port] is not None and port != dest_port:
            if self.schedule_alg == 'FIFO':
                self.handle_massage_fifo(timeline, dest_port, l2_message, all_l2messages, printing_flag)
            elif self.schedule_alg == 'Priority':
                self.handle_massage_priority(timeline, dest_port, l2_message, all_l2messages, printing_flag)
            else:
                self.handle_massage_pgps(timeline, dest_port, l2_message, all_l2messages, printing_flag)

    def message_transmitted_output(self, timeline, queue_num, all_l2messages, printing_flag):
        if self.schedule_alg == 'FIFO':
            self.message_transmitted_fifo(timeline, queue_num, all_l2messages, printing_flag)
        elif self.schedule_alg == 'Priority':
            self.message_transmitted_priority(timeline, queue_num, all_l2messages, printing_flag)
        else:
            self.message_transmitted_pgps(timeline, queue_num, all_l2messages, printing_flag)

    def handle_massage_fifo(self, timeline, dest_port, l2_message, all_l2messages, printing_flag):
        self.enqueue(l2_message, dest_port)
        if self.port_is_blocked[dest_port] is False:
            # If the port is not blocked, the switch will send the message
            self.first_message_output(timeline, dest_port, all_l2messages, printing_flag)

    def message_transmitted_fifo(self, timeline, queue_num, all_l2messages, printing_flag):
        current_time = timeline.events[0].scheduled_time

        self.port_is_blocked[queue_num] = False
        next_message = self.dequeue(queue_num)
        if next_message is None:
            return

        dest_port = queue_num
        link = self.ports[dest_port]
        time = current_time + link.transmit_delay(next_message)  # calculation of arrival time
        # = time of sending
        self.port_is_blocked[dest_port] = True
        event = Event(time, "transmitted", self.id, None, None, dest_port)
        timeline.add_event(event)
        if printing_flag == 1:
            print(f"Switch: {self.id} \033[36msending\033[0m the message (size: {next_message.message_size}) to"
                  f" port {dest_port} at time: {current_time:.6f}")
        self.send_message(timeline, dest_port, next_message, all_l2messages)

    def handle_massage_priority(self, timeline, dest_port, l2_message, all_l2messages, printing_flag):
        self.push_priority(dest_port, l2_message)
        if self.port_is_blocked[dest_port] is False:
            # If the port is not blocked, the switch will send the message
            self.first_message_priority(timeline, dest_port, all_l2messages, printing_flag)

    def first_message_priority(self, timeline, queue_num, all_l2messages, printing_flag):
        current_time = timeline.events[0].scheduled_time
        # receive the message to send
        next_message = self.queues[queue_num][0][2]
        if next_message is None:
            return

        dest_port = queue_num
        link = self.ports[queue_num]
        time = current_time + link.transmit_delay(next_message)  # calculation of arrival time
        # = time of sending
        self.port_is_blocked[queue_num] = next_message.id
        event = Event(time, "transmitted", self.id, None, next_message.id, queue_num)

        timeline.add_event(event)
        if printing_flag == 1:
            print(f"Switch: {self.id} \033[36msending\033[0m the message (size: {next_message.message_size}) "
                  f"from {next_message.src_mac} to port {dest_port} at time: {current_time:.6f}")
        self.send_message(timeline, dest_port, next_message, all_l2messages)

    def message_transmitted_priority(self, timeline, queue_num, all_l2messages, printing_flag):
        current_time = timeline.events[0].scheduled_time

        transmitted_message_id = self.port_is_blocked[queue_num]
        next_message = self.pop_priority(queue_num, transmitted_message_id)
        self.port_is_blocked[queue_num] = False
        if next_message is None:
            return
        next_message = next_message[2]

        dest_port = queue_num
        link = self.ports[dest_port]
        time = current_time + link.transmit_delay(next_message)  # calculation of arrival time
        # = time of sending
        self.port_is_blocked[dest_port] = next_message.id
        event = Event(time, "transmitted", self.id, None, None, dest_port)
        timeline.add_event(event)
        if printing_flag == 1:
            print(f"Switch: {self.id} \033[36msending\033[0m the message (size: {next_message.message_size}) "
                  f"from {next_message.src_mac} to port {dest_port} at time: {current_time:.6f}")
        self.send_message(timeline, dest_port, next_message, all_l2messages)

    def message_transmitted_pgps(self, timeline, queue_num, all_l2messages, printing_flag):
        current_time = timeline.events[0].scheduled_time
        self.port_is_blocked[queue_num] = False
        next_message = self.pgps(self.queues[queue_num])
        if next_message is None:
            return
        self.delete_tuple_by_l2(queue_num, next_message)
        dest_port = queue_num
        link = self.ports[dest_port]
        time = current_time + link.transmit_delay(next_message)  # calculation of arrival time
        # = time of sending
        self.port_is_blocked[dest_port] = True
        event = Event(time, "transmitted", self.id, None, next_message.id, dest_port)
        timeline.add_event(event)
        if printing_flag == 1:
            print(f"Switch: {self.id} \033[36msending\033[0m the message (size: {next_message.message_size}) to"
                  f" port {dest_port} at time: {current_time:.6f}")
        self.send_message(timeline, dest_port, next_message, all_l2messages)

    def print_statistics(self):
        pass

    def top_prioritys(self, queue):
        # only this first message in each priority
        tupel_packets = queue
        used_priorities = {}

        for packet in tupel_packets:
            if packet[0] not in used_priorities:
                used_priorities[packet[0]] = packet
            elif used_priorities[packet[0]][1] > packet[1]:
                used_priorities[packet[0]] = packet

        return used_priorities


    def min_key_func(self,dict):
        if dict is None:
            return None
        min_time = 0
        min_key = 0
        for key in dict.keys():
            if min_time == 0:
                min_time = dict[key]
                min_key = key
            elif dict[key] < min_time:
                min_time = dict[key]
                min_key = key
        return min_key


    def mac_to_number(self,mac):
        return int(mac.replace(':', ''), 16)


    def return_l2_by_mac(self,mac, queues):
        for queue in queues.values():
            if mac == queue[0]:
                return queue[2]

        return None

    def iter_queue(self,queues):
        pass

    def pgps(self, queues,transmission_rate=1.4e5):

        tupel_packets = self.top_prioritys(queues)

        # Use a set to store unique MAC addresses
        # Sum the numeric representations of unique MAC addresses
        total_sum = sum(self.mac_to_number(mac) for mac in tupel_packets)
        if(total_sum == 0):
            return None
        rate = transmission_rate / total_sum  # find rate
        end_times = {}
        min = 0
        for p in tupel_packets.values():
            end_times[p[0]] = p[2].message_size / (rate * self.mac_to_number(p[0]))  # TODO: need to check if true
        min = self.min_key_func(end_times)

        return self.return_l2_by_mac(min, tupel_packets)

    def handle_massage_pgps(self,timeline, dest_port, l2_message, all_l2messages, printing_flag):
        self.push_priority(dest_port, l2_message)
        if self.port_is_blocked[dest_port] is False:
            # If the port is not blocked, the switch will send the message
            self.first_message_pgps(timeline, dest_port, all_l2messages, printing_flag)

    def delete_tuple_by_l2(self,queue_num,l2_message):
        for tuple in self.queues[queue_num]:
            if tuple[2] == l2_message:
                self.queues[queue_num].remove(tuple)
        return

    def first_message_pgps(self, timeline, queue_num, all_l2messages, printing_flag):
        current_time = timeline.events[0].scheduled_time
        # receive the message to send
        next_message = self.queues[queue_num][0][2]
        if next_message is None:
            return
        self.delete_tuple_by_l2(queue_num, next_message)
        dest_port = queue_num
        link = self.ports[queue_num]
        time = current_time + link.transmit_delay(next_message)  # calculation of arrival time
        # = time of sending
        self.port_is_blocked[queue_num] = next_message.id
        event = Event(time, "transmitted", self.id, None, next_message.id, queue_num)

        timeline.add_event(event)
        if printing_flag == 1:
            print(f"Switch: {self.id} \033[36msending\033[0m the message (size: {next_message.message_size}) "
                  f"from {next_message.src_mac} to port {dest_port} at time: {current_time:.6f}")
        self.send_message(timeline, dest_port, next_message, all_l2messages)