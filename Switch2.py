import queue
import math
import copy
from Switch import Switch
from Event import Event
import random


class SwitchLab2(Switch):
    def __init__(self, num_ports, mac_table_size, q_type="input", is_fluid=False, schedule_alg='FIFO', log_file=None,
                 seed=42, ttl=10):
        super().__init__(num_ports, mac_table_size, log_file, ttl)
        if seed is not None:
            random.seed(seed)

        self.q_type = q_type
        self.is_fluid = is_fluid
        self.schedule_alg = schedule_alg
        self.queues = self.configure_queues()
        self.totalHoLTime = 0
        self.queue_to_HoLTime = {}
        if self.q_type == 'input' or self.q_type == 'output':
            for i in range(num_ports):
                self.queue_to_HoLTime[i] = 0
        else:
            for i in range(num_ports):
                for j in range(num_ports):
                    self.queue_to_HoLTime[(i, j)] = 0
        self.port_is_blocked = [False] * self.num_ports
        self.flooding_from_port = [False] * self.num_ports
        self.flooding_tabel = [[False for _ in range(self.num_ports)] for _ in range(self.num_ports)]
        self.start_to_flood = False

    def configure_queues(self):
        if self.q_type == 'input' or self.q_type == 'output':
            return [queue.Queue() for _ in range(self.num_ports)]
        elif self.q_type == 'virtual_output':
            return [[queue.Queue() for _ in range(self.num_ports)] for _ in range(self.num_ports)]
        else:
            raise ValueError("Invalid queue type")

    def get_real_queue(self, queue_num):
        # Here we created a bijection between ordered pair and integer
        # The ordered pair is used to represent the virtual output queue
        # The integer is used to represent the input and output queues
        # This bijection is used to simplify the code
        if self.q_type == 'virtual_output' or self.q_type == 'input':
            return [math.floor(queue_num / self.num_ports), queue_num % self.num_ports]
        else:
            return [queue_num]

    def get_fake_queue(self, queue_num):
        # Here is the inverse of the bijection
        if self.q_type == 'virtual_output' or self.q_type == 'input':
            return queue_num[0] * self.num_ports + queue_num[1]
        else:
            return queue_num

    def enqueue(self, message, queue_num):
        if self.q_type == 'input' or self.q_type == 'output':
            self.queues[queue_num].put(message)
        elif self.q_type == 'virtual_output':
            self.queues[queue_num[0]][queue_num[1]].put(message)

    def dequeue(self, queue_num):
        # This function is used to dequeue a message from the queue
        # The function returns the first message after removing
        if self.q_type == 'input' or self.q_type == 'output':
            self.queues[queue_num].get()
            if self.queues[queue_num].empty():
                return None
            return self.queues[queue_num].queue[0]
        elif self.q_type == 'virtual_output':
            self.queues[self.get_real_queue(queue_num)[0]][self.get_real_queue(queue_num)[1]].get()
            if self.queues[self.get_real_queue(queue_num)[0]][self.get_real_queue(queue_num)[1]].empty():
                return None
            return self.queues[self.get_real_queue(queue_num)[0]][self.get_real_queue(queue_num)[1]].queue[0]

    def handle_message(self, l2_message, all_l2messages, timeline, current_time, link_id, printing_flag):
        src_mac = l2_message.src_mac
        dst_mac = l2_message.dst_mac
        port = self.link_to_port(link_id)

        if printing_flag == 1:
            print(f"Switch: {self.id} \033[34mreceived\033[0m a message (size: {l2_message.message_size}) from port"
                  f" {port} at time: {current_time:.6f}, MAC table updated")
            print(f"Source MAC: {src_mac} Destination MAC: {dst_mac}")
        self.update_mac_table(src_mac, port, current_time, printing_flag)

        if self.q_type == 'input':
            self.handle_message_input(l2_message, all_l2messages, timeline, current_time, link_id, printing_flag)
        elif self.q_type == 'output':
            self.handle_message_output(l2_message, all_l2messages, timeline, current_time, link_id, printing_flag)
        elif self.q_type == 'virtual_output':
            self.handle_message_virtual_output(l2_message, all_l2messages, timeline, current_time, link_id,
                                               printing_flag)

    def handle_message_input(self, l2_message, all_l2messages, timeline, current_time, link_id, printing_flag):
        dst_mac = l2_message.dst_mac
        port = self.link_to_port(link_id)
        dest_port = self.find_port(dst_mac, current_time)
        if port == dest_port:  # if the destination is the same as the source drop the message
            return

        if self.queues[port].empty():
            # try to send the message
            self.enqueue(l2_message, port)
            self.update_flooding_tabel(l2_message, port, current_time)
            self.try_send_message_input(all_l2messages, timeline, current_time, port, printing_flag)
        else:
            self.enqueue(l2_message, port)

    def try_send_message_input(self, all_l2messages, timeline, current_time, in_port, printing_flag):
        l2_message = self.queues[in_port].queue[0]
        for out_port in range(self.num_ports):
            if self.flooding_tabel[in_port][out_port] is False or self.flooding_tabel[in_port][out_port]\
                    == "transmitting":  # The message should not be sent to this port
                continue
            if self.port_is_blocked[out_port] is True:  # The message should be sent to this port, but it is blocked
                if self.queue_to_HoLTime[in_port] == 0:
                    self.queue_to_HoLTime[in_port] = current_time
            else:  # The message should be sent to this port, and it is not blocked. send to message
                # if for flooding duplicate the message
                if self.flooding_from_port[in_port] is True:  # duplicate the message if it is flooding
                    duplicated_message = copy.copy(l2_message)
                    l2_message = duplicated_message
                self.flooding_tabel[in_port][out_port] = "transmitting"
                self.port_is_blocked[out_port] = True
                link = self.ports[out_port]
                time = current_time + link.transmit_delay(l2_message)  # calculation of arrival time
                # = time of sending
                event = Event(time, "transmitted", self.id, None, None, self.get_fake_queue([in_port, out_port]))
                timeline.add_event(event)
                if printing_flag == 1:
                    print(f"Switch: {self.id} \033[36msending\033[0m the message (size: {l2_message.message_size}) to"
                          f" port {out_port} at time: {current_time:.6f}")
                self.send_message(timeline, out_port, l2_message, all_l2messages)

    def handle_message_output(self, l2_message, all_l2messages, timeline, current_time, link_id, printing_flag):
        dst_mac = l2_message.dst_mac
        port = self.link_to_port(link_id)

        dest_port = self.find_port(dst_mac, current_time)
        if dest_port is not None:  # If the destination port is found in the MAC table
            if self.ports[dest_port] is not None:  # If the destination port is connected
                if port != dest_port:  # if not the switch should drop the message
                    self.enqueue(l2_message, dest_port)
                    if self.port_is_blocked[dest_port] is False:
                        # If the port is not blocked, the switch will send the message
                        self.first_message_output(timeline, dest_port, all_l2messages, printing_flag)
            else:  # that if the link was disconnected
                pass
        else:
            if printing_flag == 1:
                print(f"Switch: {self.id} \033[35m will flood\033[0m the message (size: {l2_message.message_size}) "
                      f"at time: {current_time:.6f}")
            for out_port, link in enumerate(self.ports):
                if out_port != port and link is not None:
                    duplicated_message = copy.copy(l2_message)
                    self.enqueue(duplicated_message, out_port)
                    if self.port_is_blocked[out_port] is False:
                        # If the port is not blocked, the switch will send the message
                        self.first_message_output(timeline, out_port, all_l2messages, printing_flag)

    def handle_message_virtual_output(self, l2_message, all_l2messages, timeline, current_time, link_id, printing_flag):
        dst_mac = l2_message.dst_mac
        port = self.link_to_port(link_id)

        dest_port = self.find_port(dst_mac, current_time)
        queue_num = [port, dest_port]
        if dest_port is not None:  # If the destination port is found in the MAC table
            if self.ports[dest_port] is not None:  # If the destination port is connected
                if port != dest_port:  # if not the switch should drop the message
                    self.enqueue(l2_message, queue_num)
                    # if the message is the first message in the queue then try to send it
                    if self.queues[port][dest_port].qsize() == 1:
                        if self.port_is_blocked[dest_port] is False:
                            # If the port is not blocked, the switch will send the message
                            self.first_message_virtual_output(timeline, queue_num, all_l2messages, printing_flag)
                        else:
                            if self.queue_to_HoLTime[(port, dest_port)] == 0:
                                self.queue_to_HoLTime[(port, dest_port)] = current_time
            else:  # that if the link was disconnected
                pass
        else:
            if printing_flag == 1:
                print(f"Switch: {self.id} \033[35m will flood\033[0m the message (size: {l2_message.message_size}) "
                      f"at time: {current_time:.6f}")
            for out_port, link in enumerate(self.ports):
                if out_port != port and link is not None:
                    queue_num = [port, out_port]
                    duplicated_message = copy.copy(l2_message)
                    self.enqueue(duplicated_message, queue_num)
                    # if the message is the first message in the queue then try to send it
                    if self.queues[port][out_port].qsize() == 1:
                        if self.port_is_blocked[out_port] is False:
                            # If the port is not blocked, the switch will send the message
                            self.first_message_virtual_output(timeline, queue_num, all_l2messages, printing_flag)
                        else:
                            if self.queue_to_HoLTime[(port, out_port)] == 0:
                                self.queue_to_HoLTime[(port, out_port)] = current_time

    def message_transmitted(self, timeline, queue_num, all_l2messages, printing_flag):
        if printing_flag == 1:
            temp = self.get_real_queue(queue_num)
            if self.q_type == 'input' or self.q_type == 'virtual_output':
                temp = temp[1]

            print(f"Switch: {self.id} \033[38;5;90mtransmitted\033[0m a message to port {temp} at time: "
                  f"{timeline.events[0].scheduled_time:.6f}")

        if self.q_type == 'input':
            self.message_transmitted_input(timeline, queue_num, all_l2messages, printing_flag)
        elif self.q_type == 'output':
            self.message_transmitted_output(timeline, queue_num, all_l2messages, printing_flag)
        else:
            self.message_transmitted_virtual_output(timeline, queue_num, all_l2messages, printing_flag)

    def message_transmitted_input(self, timeline, queue_num, all_l2messages, printing_flag):
        # We will first unblock the port the message was sent from
        # Then we will check if there is a message that was blocked, we will choose the oldest one
        # If we found one it will be sent
        # We will dequeue the message that was transmitted then try to send the message that become the head of line
        current_time = timeline.events[0].scheduled_time
        input_port = self.get_real_queue(queue_num)[0]
        output_port = self.get_real_queue(queue_num)[1]
        self.port_is_blocked[output_port] = False
        if self.flooding_tabel[input_port][output_port] != "transmitting":
            raise ValueError("not transmitting message was transmitted")
        self.flooding_tabel[input_port][output_port] = False

        # we will now find the queue which is waiting to send to output_port the longest time (if exists)
        oldest_port = None
        min_time = None
        for port in range(self.num_ports):
            if self.flooding_tabel[port][output_port] is True:
                if min_time is None:
                    oldest_port = port
                    min_time = self.queue_to_HoLTime[port]
                elif self.queue_to_HoLTime[port] < min_time:
                    oldest_port = port
                    min_time = self.queue_to_HoLTime[port]
        # if found send it
        if oldest_port is not None:
            self.try_send_message_input(all_l2messages, timeline, current_time, oldest_port, printing_flag)
            if self.everything_transmitted(oldest_port):
                self.totalHoLTime += current_time - self.queue_to_HoLTime[oldest_port]
                self.queue_to_HoLTime[oldest_port] = 0

        # check if the message that was transmitted has finished sending
        if self.queues[input_port].empty():
            raise Exception("Queue is empty")
        if self.is_finished_sending(input_port) is False:
            return
        # dequeue the message that was transmitted and try to send the message that become the head of line
        next_message = self.dequeue(input_port)
        if next_message is not None:
            self.update_flooding_tabel(next_message, input_port, current_time)
            self.try_send_message_input(all_l2messages, timeline, current_time, input_port, printing_flag)
            # if self.is_finished_sending(input_port):
            #     self.totalHoLTime += current_time - self.queue_to_HoLTime[input_port]
            #     self.queue_to_HoLTime[input_port] = 0

    def message_transmitted_output(self, timeline, queue_num, all_l2messages, printing_flag):
        current_time = timeline.events[0].scheduled_time

        self.port_is_blocked[queue_num] = False
        self.totalHoLTime += self.queue_to_HoLTime[queue_num]
        self.queue_to_HoLTime[queue_num] = 0
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

    def message_transmitted_virtual_output(self, timeline, queue_num, all_l2messages, printing_flag):
        # We will first unblock the port the message was sent from
        # Then we will check if there is a message that was blocked, we will choose the oldest one
        # If we found one it will be sent
        # We will dequeue the message that was transmitted then try to send the message that become the head of line
        current_time = timeline.events[0].scheduled_time
        input_port = self.get_real_queue(queue_num)[0]
        output_port = self.get_real_queue(queue_num)[1]
        self.port_is_blocked[output_port] = False
        next_message = self.dequeue(queue_num)
        self.queue_to_HoLTime[queue_num] = 0

        # we will now find the queue which is waiting to send to output_port the longest time (if exists)
        oldest_port = None
        min_time = None
        for port in range(self.num_ports):
            if port == input_port:
                continue
            if self.queues[port][output_port].empty() is False:
                if min_time is None:
                    oldest_port = port
                    min_time = self.queue_to_HoLTime[(port, output_port)]
                elif self.queue_to_HoLTime[(port, output_port)] < min_time:
                    oldest_port = port
                    min_time = self.queue_to_HoLTime[(port, output_port)]
        # if found send it
        if oldest_port is not None:
            # TODO: send the message
            dest_port = output_port
            message = self.queues[oldest_port][output_port].queue[0]
            link = self.ports[dest_port]
            time = current_time + link.transmit_delay(message)  # calculation of arrival time
            # = time of sending
            self.port_is_blocked[dest_port] = True
            event = Event(time, "transmitted", self.id, None, None, self.get_fake_queue([oldest_port, dest_port]))
            timeline.add_event(event)
            if printing_flag == 1:
                print(f"Switch: {self.id} \033[36msending\033[0m the message (size: {message.message_size}) to"
                      f" port {dest_port} at time: {current_time:.6f}")
            self.send_message(timeline, dest_port, message, all_l2messages)
            # TODO: update the HoLTime
            if self.queue_to_HoLTime[(oldest_port, output_port)] != 0:
                self.totalHoLTime += current_time - self.queue_to_HoLTime[(oldest_port, output_port)]
                self.queue_to_HoLTime[(oldest_port, output_port)] = 0

        # check if there is a next message to send
        if next_message is None:
            return
        if not self.queues[input_port]:
            raise Exception("Queue is empty")

        if self.port_is_blocked[output_port] is False:
            # If the port is not blocked, the switch will send the message
            # TODO: send the message
            dest_port = output_port
            link = self.ports[dest_port]
            time = current_time + link.transmit_delay(next_message)  # calculation of arrival time
            # = time of sending
            self.port_is_blocked[dest_port] = True
            event = Event(time, "transmitted", self.id, None, None, self.get_fake_queue([input_port, dest_port]))
            timeline.add_event(event)
            if printing_flag == 1:
                print(f"Switch: {self.id} \033[36msending\033[0m the message (size: {next_message.message_size}) to"
                      f" port {dest_port} at time: {current_time:.6f}")
            self.send_message(timeline, dest_port, next_message, all_l2messages)
        else:
            self.queue_to_HoLTime[(input_port, output_port)] = current_time

    def first_message_output(self, timeline, queue_num, all_l2messages, printing_flag):
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

    def first_message_virtual_output(self, timeline, queue_num, all_l2messages, printing_flag):
        current_time = timeline.events[0].scheduled_time
        # receive the message to send

        next_message = self.queues[queue_num[0]][queue_num[1]].queue[0]
        if next_message is None:
            return

        dest_port = queue_num[1]
        link = self.ports[dest_port]
        time = current_time + link.transmit_delay(next_message)  # calculation of arrival time
        # = time of sending
        self.port_is_blocked[dest_port] = True
        event = Event(time, "transmitted", self.id, None, None, self.get_fake_queue(queue_num))
        timeline.add_event(event)
        if printing_flag == 1:
            print(f"Switch: {self.id} \033[36msending\033[0m the message (size: {next_message.message_size}) to"
                  f" port {dest_port} at time: {current_time:.6f}")
        self.send_message(timeline, dest_port, next_message, all_l2messages)

    def update_flooding_tabel(self, message, in_port, current_time):
        self.flooding_tabel[in_port] = [False] * self.num_ports
        self.flooding_from_port[in_port] = False
        dst_mac = message.dst_mac
        dest_port = self.find_port(dst_mac, current_time)
        if dest_port is not None:  # If the destination port is found in the MAC table
            if self.ports[dest_port] is not None:  # If the destination port is connected
                if in_port != dest_port:  # if not the switch should drop the message
                    self.flooding_tabel[in_port][dest_port] = True
        else:
            for port in range(self.num_ports):
                if port != in_port and self.ports[port] is not None:
                    self.flooding_tabel[in_port][port] = True
            self.flooding_from_port[in_port] = True

    def is_finished_sending(self, in_port):
        for out_port in range(self.num_ports):
            if self.flooding_tabel[in_port][out_port] is True or self.flooding_tabel[in_port][out_port] \
                    == "transmitting":
                return False
        return True

    def everything_transmitted(self, in_port):
        for out_port in range(self.num_ports):
            if self.flooding_tabel[in_port][out_port] is True:
                return False
        return True

    def print_statistics(self):
        print(f"Switch: {self.id} \033[32mTotal time\033[0m in the Head of Line: {self.totalHoLTime:.6f}")
