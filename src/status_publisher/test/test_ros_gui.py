import os
import time
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication
import pytest
import rclpy
from rclpy.context import Context
from rclpy.executors import SingleThreadedExecutor
from rclpy.parameter import Parameter
from status_interfaces.msg import SystemStatus

from status_publisher.sys_status_gui import StatusWindow, SysStatusGui
from status_publisher.sys_status_pub import SysStatusPub


@pytest.fixture(scope='module')
def app():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    application = QApplication.instance() or QApplication([])
    yield application


def test_gui_fields_stale_and_recovery(app):
    window = StatusWindow(stale_timeout=3.0)
    message = SystemStatus(
        hostname='test-host', cpu_percent=23.5, memory_percent=50.0,
        memory_total=8192.0, memory_available=4096.0, net_sent=10.0, net_recv=20.0,
    )
    message.stamp.sec = 1700000000
    try:
        assert '等待' in window.connection.text()
        window.show_status(message)
        assert window.values['hostname'].text() == 'test-host'
        assert window.values['cpu_percent'].value() == 235
        assert window.values['memory_percent'].format() == '50.0%'
        assert window.values['memory_total'].text() == '8,192.00 MiB'
        assert window.values['memory_available'].text() == '4,096.00 MiB'
        assert window.values['net_sent'].text() == '10.00 MiB'
        assert window.values['net_recv'].text() == '20.00 MiB'
        assert '2023-' in window.values['stamp'].text()
        with patch('status_publisher.sys_status_gui.time.monotonic',
                   return_value=window.last_received + 4.0):
            window.check_stale()
        assert '未收到数据' in window.connection.text()
        window.show_status(message)
        assert '正在接收' in window.connection.text()
    finally:
        window.close()


def test_publisher_to_gui_over_dds(app):
    context = Context()
    rclpy.init(context=context)
    executor = SingleThreadedExecutor(context=context)
    publisher = subscriber = None
    window = StatusWindow()
    try:
        publisher = SysStatusPub(
            context=context,
            parameter_overrides=[Parameter('publish_period', value=0.1)],
        )
        subscriber = SysStatusGui(window, context=context)
        executor.add_node(publisher)
        executor.add_node(subscriber)
        deadline = time.monotonic() + 10.0
        while window.last_received is None and time.monotonic() < deadline:
            executor.spin_once(timeout_sec=0.05)
            app.processEvents()
        assert window.last_received is not None, 'No status received through DDS'
        assert window.values['hostname'].text() == publisher.sampler.hostname
        assert window.values['memory_total'].text() != '—'
        assert '正在接收' in window.connection.text()
        previous = window.last_received
        while window.last_received == previous and time.monotonic() < deadline:
            executor.spin_once(timeout_sec=0.05)
            app.processEvents()
        assert window.last_received > previous
    finally:
        executor.shutdown()
        for node in (publisher, subscriber):
            if node is not None:
                node.destroy_node()
        context.shutdown()
        window.close()
