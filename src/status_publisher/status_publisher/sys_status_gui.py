from datetime import datetime, timezone
import math
import signal
import sys
import time

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QFormLayout, QLabel, QProgressBar, QVBoxLayout, QWidget,
)
import rclpy
from rclpy.executors import ExternalShutdownException, SingleThreadedExecutor
from rclpy.node import Node
from rclpy.utilities import remove_ros_args
from rcl_interfaces.msg import ParameterDescriptor
from status_interfaces.msg import SystemStatus


class StatusWindow(QWidget):
    def __init__(self, stale_timeout=3.0):
        super().__init__()
        self.stale_timeout = stale_timeout
        self.last_received = None
        self.setWindowTitle('ROS 2 系统状态监视器')
        self.resize(540, 370)
        layout = QVBoxLayout(self)
        title = QLabel('系统实时状态')
        title.setStyleSheet('font-size: 22px; font-weight: bold;')
        layout.addWidget(title)
        self.connection = QLabel('等待状态消息…')
        layout.addWidget(self.connection)
        form = QFormLayout()
        form.setSpacing(14)
        layout.addLayout(form)
        self.values = {}
        for field, caption in [
            ('stamp', '记录时间（本地）'), ('hostname', '主机名'),
            ('cpu_percent', 'CPU 使用率'), ('memory_percent', '内存使用率'),
            ('memory_total', '内存总大小'), ('memory_available', '剩余可用内存'),
            ('net_recv', '网络累计接收'), ('net_sent', '网络累计发送'),
        ]:
            if field.endswith('_percent'):
                widget = QProgressBar()
                widget.setRange(0, 1000)
                widget.setValue(0)
                widget.setFormat('等待数据')
            else:
                widget = QLabel('—')
                widget.setTextFormat(Qt.PlainText)
                widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.values[field] = widget
            form.addRow(caption, widget)
        note = QLabel('容量单位：MiB（1024² 字节）；网络为网卡累计流量，非每秒速率。')
        note.setWordWrap(True)
        note.setStyleSheet('color: #666;')
        layout.addWidget(note)
        self.stale_timer = QTimer(self)
        self.stale_timer.timeout.connect(self.check_stale)
        self.stale_timer.start(250)

    def show_status(self, message):
        self.last_received = time.monotonic()
        self.connection.setText('● 正在接收实时数据')
        self.connection.setStyleSheet('color: #16803a;')
        seconds = message.stamp.sec + message.stamp.nanosec / 1e9
        stamp = datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone()
        self.values['stamp'].setText(stamp.isoformat(sep=' ', timespec='seconds'))
        self.values['hostname'].setText(message.hostname)
        for field in ('cpu_percent', 'memory_percent'):
            value = getattr(message, field)
            bar = self.values[field]
            if math.isfinite(value):
                bar.setValue(round(max(0.0, min(100.0, value)) * 10))
                bar.setFormat(f'{value:.1f}%')
            else:
                bar.setValue(0)
                bar.setFormat('数据无效')
        for field in ('memory_total', 'memory_available', 'net_recv', 'net_sent'):
            self.values[field].setText(f'{getattr(message, field):,.2f} MiB')

    def check_stale(self):
        if self.last_received is None:
            return
        elapsed = time.monotonic() - self.last_received
        if elapsed > self.stale_timeout:
            self.connection.setText(f'⚠ 已 {elapsed:.1f} 秒未收到数据（显示上次记录）')
            self.connection.setStyleSheet('color: #b45309;')


class SysStatusGui(Node):
    def __init__(self, window, **kwargs):
        super().__init__('sys_status_gui', **kwargs)
        timeout = self.declare_parameter(
            'stale_timeout', 3.0,
            ParameterDescriptor(read_only=True),
        ).value
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('stale_timeout must be finite and positive')
        window.stale_timeout = timeout
        self.subscription = self.create_subscription(
            SystemStatus, 'system_status', window.show_status, 1,
        )


def main(args=None):
    ros_args = sys.argv if args is None else [sys.argv[0], *args]
    rclpy.init(args=ros_args)
    app = QApplication(remove_ros_args(args=ros_args))
    node = None
    executor = SingleThreadedExecutor()
    timer = QTimer()
    old_sigint = signal.signal(signal.SIGINT, lambda *_: app.quit())
    old_sigterm = signal.signal(signal.SIGTERM, lambda *_: app.quit())
    try:
        window = StatusWindow()
        node = SysStatusGui(window)
        executor.add_node(node)

        def poll_ros():
            if not rclpy.ok():
                app.quit()
                return
            try:
                executor.spin_once(timeout_sec=0.0)
            except ExternalShutdownException:
                app.quit()

        timer.timeout.connect(poll_ros)
        timer.start(20)
        window.show()
        app.exec_()
    finally:
        timer.stop()
        executor.shutdown()
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        signal.signal(signal.SIGINT, old_sigint)
        signal.signal(signal.SIGTERM, old_sigterm)
