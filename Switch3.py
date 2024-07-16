import queue
import math
import copy
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
        self.total_packet_size = 0
        self.transmission_rate = 1.4
        self.end_point = 0  #self.total_packet_size * self.transmission_rate

    def configure_queues(self):
        if self.schedule_alg == 'FIFO':
            return [queue.Queue() for _ in range(self.num_ports)]
        elif self.schedule_alg == 'Priority':
            return [[] for _ in range(self.num_ports)]
        else:
            return [queue.Queue() for _ in range(self.num_ports)]       # TODO

    def push_priority(self, queue_num: int, message: L2Message):
        heapq.heappush(self.queues[queue_num], (message.src_mac, next(self.counters[queue_num]), message))

    def pop_priority(self, queue_num):
        if self.queues[queue_num]:
            return heapq.heappop(self.queues[queue_num])
        else:
            return None

    def handle_message_output(self, l2_message, all_l2messages, timeline, current_time, link_id, printing_flag):
        dst_mac = l2_message.dst_mac
        port = self.link_to_port(link_id)

        dest_port = self.find_port(dst_mac, current_time)
        if dest_port is None:
            # If the destination port is not found, flood the message, but we disable flooding in Lab 3
            # We will send the message to the next port in the list
            dest_port = (port + 1) % self.num_ports

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

    def first_message_output(self, timeline, queue_num, all_l2messages, printing_flag): # TODO: no change
        current_time = timeline.events[0].scheduled_time
        # receive the message to send
        next_message = self.queues[queue_num].queue[0]
        #  update the HoL time
        self.totalHoLTime += self.queue_to_HoLTime[queue_num]
        self.queue_to_HoLTime[queue_num] = 0
        if next_message is None:
            return

        dest_port = queue_num
        link = self.ports[queue_num]
        time = current_time + link.transmit_delay(next_message)  # calculation of arrival time
        # = time of sending
        self.port_is_blocked[queue_num] = True
        event = Event(time, "transmitted", self.id, None, None, queue_num)

        timeline.add_event(event)
        if printing_flag == 1:
            print(f"Switch: {self.id} \033[36msending\033[0m the message (size: {next_message.message_size}) to"
                  f" port {dest_port} at time: {current_time:.6f}")
        self.send_message(timeline, dest_port, next_message, all_l2messages)

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
            self.first_message_output(timeline, dest_port, all_l2messages, printing_flag)

    def first_message_priority(self, timeline, queue_num, all_l2messages, printing_flag):
        current_time = timeline.events[0].scheduled_time
        # receive the message to send
        next_message = self.queues[queue_num][0]
        if next_message is None:
            return

        dest_port = queue_num
        link = self.ports[queue_num]
        time = current_time + link.transmit_delay(next_message)  # calculation of arrival time
        # = time of sending
        self.port_is_blocked[queue_num] = True
        event = Event(time, "transmitted", self.id, None, None, queue_num)

        timeline.add_event(event)
        if printing_flag == 1:
            print(f"Switch: {self.id} \033[36msending\033[0m the message (size: {next_message.message_size}) to"
                  f" port {dest_port} at time: {current_time:.6f}")
        self.send_message(timeline, dest_port, next_message, all_l2messages)

    def message_transmitted_priority(self, timeline, queue_num, all_l2messages, printing_flag):
        current_time = timeline.events[0].scheduled_time

        self.port_is_blocked[queue_num] = False
        next_message = self.pop_priority(queue_num)
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

    def handle_massage_pgps(self, timeline, dest_port, l2_message, all_l2messages, printing_flag):
        pass

    def message_transmitted_pgps(self, timeline, queue_num, all_l2messages, printing_flag):
        current_time = timeline.events[0].scheduled_time
        self.port_is_blocked[queue_num] = False
        next_message = self.pgps(self.queues[queue_num])
        self.queues[queue_num].remove(next_message)
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

    def print_statistics(self):
        pass

    def top_prioritys(self, queues, queue_num=0):
        tupel_packets = queues  # [queue_num]
        used_proritys = {}
        for packet in tupel_packets:
            if packet[0] not in used_proritys:
                used_proritys[packet[0]] = packet
            elif used_proritys[packet[0]][1] > packet[1]:
                used_proritys[packet[0]] = packet

        return used_proritys


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
        print(min_time)
        return min_key


    def mac_to_number(self,mac):
        return int(mac.replace(':', ''), 16)


    def return_l2_by_mac(self,mac, queues):
        for queue in queues.values():
            if mac == queue[0]:
                return queue[2]

        return None


    def pgps(self, queues,transmission_rate = 1.4):

        tupel_packets = self.top_prioritys(queues)

        # Use a set to store unique MAC addresses
        # Sum the numeric representations of unique MAC addresses
        total_sum = sum(self.mac_to_number(mac) for mac in tupel_packets)

        rate = transmission_rate / total_sum  # find rate
        end_times = {}
        min = 0
        for p in tupel_packets.values():
            end_times[p[0]] = p[2].message_size / (rate * self.mac_to_number(p[0]))  # TODO: need to check if true
        min = self.min_key_func(end_times)

        return self.return_l2_by_mac(min, tupel_packets)

