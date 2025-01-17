"""
File:           CommunicationManager.py
Date:           February 2024
Description:    Manage communication between entities (robot, remote, ...)
                Send, receive, order messages.
Author:         Nordine HIDA
Modifications:
"""

from RobotUpInitializer import *


class CommunicationManager:
    """
    Manage communication between entities (robot, remote, ...)
    Send, receive, order messages by priority.
    """

    def __init__(self, robot: RobotUpInitializer):
        """
        Initialize the CommunicationManager object with the specified robot. \n
        |!| the emitter of the robot should be called "emitter" (default name in webots) \n
        |!| the receiver of the robot should be called "receiver" (default name in webots)

        Args:
            robot (RobotUpInitializer): The robot object (a remote can be considered as a robot)
        """
        self.robot = robot
        self.emitter = robot.getDevice("emitter")
        self.receiver = robot.getDevice("receiver")
        self.time_step = int(self.robot.getBasicTimeStep())
        self.max_send_counter = 5

    def send_message(self, msg: Message):
        """
        Send a message to the appropriate recipient. \n
        id_sender;message_type;payload;recipient
        Args:
            msg (Message): The message to be sent.
        """
        # Construct the message to be sent
        outgoing_msg = "{};{};{};{};{}".format(msg.id_sender, msg.message_type, msg.send_counter+1, msg.payload, msg.recipient)
        print(self.robot.getName(), " : Send : ", outgoing_msg)
        self.emitter.send(outgoing_msg)
        self.robot.step(self.time_step)

    def send_message_all(self, id_sender: str, message_type: MESSAGE_TYPE_PRIORITY, send_counter: int,
                         payload: str = ""):
        """
        Send the message to all known robots.
        |!| It didn't mean that they will receive it (they should be in range to receive it)

        Args:
            id_sender (str): ID of the sender (webots's name).
            message_type (MESSAGE_TYPE_PRIORITY): Message type from the enumeration MESSAGE_TYPE_PRIORITY.
            send_counter (int): Number of times the message has been transmitted.
            payload (str): content of the message ("" by default).
        """
        for robot_name in self.robot.known_robots:
            self.send_message(Message(id_sender, message_type, send_counter, payload, robot_name))

    def receive_message(self):
        """
        Receive messages from the communication channel.
        If there is no recipient, or the robot is the recipient, It adds it in its list of messages.
        As soon as it has been read the message is deleted from the receiver's buffer.
        """
        self.robot.step(self.time_step)

        # Iterate over the received messages based on the queue length
        for _ in range(self.receiver.getQueueLength()):
            incoming_msg = self.receiver.getString()
            self.receiver.nextPacket()
            try:
                if incoming_msg:
                    # Split the incoming message into its parts
                    id_sender, message_type, send_counter, payload, recipient = incoming_msg.split(";")

                    send_counter = int(send_counter)
                    # If there is no recipient, or I'm the recipient or the counter is < Max, consider the message
                    if recipient == "" or recipient == self.robot.getName() and send_counter < self.max_send_counter:
                        # Print the message for debugging purposes
                        print_message_type = message_type.replace("MESSAGE_TYPE_PRIORITY.", "")
                        print(self.robot.getName(), " : Receive : ", id_sender, ";", print_message_type, ";",
                              send_counter, ";", payload, ";", recipient)

                        # Create and add the Message to the robot's list ordered by priority
                        self.robot.append(Message(id_sender, message_type, send_counter, payload, recipient))

            except ValueError:
                # If there are not enough parts in the message, or it cannot be split properly
                raise ValueError("Invalid message format: '{}'".format(incoming_msg))

    @staticmethod
    def is_the_message_prioritary(msg: Message, current_task: MESSAGE_TYPE_PRIORITY) -> bool:
        """
        Process a message to determine if its priority is higher than a current tasks.

        Args:
            msg (Message): The message to be processed.
            current_task (MESSAGE_TYPE_PRIORITY): The current task to compare against.

        Returns:
            bool: True if the message priority is higher than the current task, False otherwise.
        """

        # Compare the priority of the message with the priority threshold

        return MESSAGE_TYPE_PRIORITY.priority(str(msg.message_type)) > MESSAGE_TYPE_PRIORITY.priority(str(current_task))

    def clear_messages(self):
        """
        Clear all messages in the message's queue and robot's list
        """
        while self.receiver.getQueueLength() > 0:
            self.receiver.nextPacket()
        self.robot.list_messages.clear()
        print(self.robot.getName(), " : All messages cleared")
