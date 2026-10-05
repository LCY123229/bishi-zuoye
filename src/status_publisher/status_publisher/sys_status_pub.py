import math
import signal
import time

import rclpy
from rclpy.clock import Clock, ClockType
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rcl_interfaces.msg import ParameterDescriptor
from status_interfaces.msg import SystemStatus

from status_publisher.metrics import SystemSampler


class SysStatusPub(Node):
    def __init__(self, **kwargs):
        super().__init__('sys_status_pub', **kwargs)
        period = self.declare_parameter(
            'publish_period', 1.0,
            ParameterDescriptor(read_only=True),
        ).value
        if not math.isfinite(period) or period < 0.1:
            raise ValueError('publish_period must be a finite float >= 0.1 seconds')
        self.sampler = SystemSampler()
        self.publisher = self.create_publisher(SystemStatus, 'system_status', 1)
        self.timer = self.create_timer(
            period, self.publish_status, clock=Clock(clock_type=ClockType.STEADY_TIME),
        )
        self.get_logger().info(f'Publishing system_status every {period:.2f} s')

    def publish_status(self):
        try:
            metrics = self.sampler.sample()
        except (OSError, RuntimeError) as error:
            self.get_logger().error(f'Cannot sample system metrics: {error}')
            return
        message = SystemStatus(**metrics)
        message.stamp.sec, message.stamp.nanosec = divmod(time.time_ns(), 10**9)
        self.publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = SysStatusPub()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
