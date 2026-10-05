# ROS 2 系统状态监视器

Ubuntu 22.04 / ROS 2 Humble / Python 3.10 / PyQt5。

- `status_interfaces`：定义 `SystemStatus` 消息。
- `status_publisher`：采集系统状态并发布到 `/system_status`，Qt 窗口订阅显示。

显示采样时间、主机名、CPU 使用率、内存使用率、总内存、可用内存和网络收发量。
容量单位为 MiB，网络数值为全部网卡累计流量。可用内存包含可回收缓存。

## 构建

安装好 ROS 2 Humble 后，退出 Conda 环境，在项目根目录执行：

```bash
sudo apt install python3-colcon-common-extensions python3-psutil python3-pyqt5 \
  python3-pytest ros-humble-rosidl-default-generators ros-humble-rosidl-default-runtime
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## 运行

每个新终端都需先加载环境。在项目根目录执行：

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch status_publisher system_monitor.launch.py
```

默认每秒更新，超过 3 秒未收到消息时提示数据过期。关闭窗口或按 Ctrl+C 结束运行。

可选参数：

```bash
ros2 launch status_publisher system_monitor.launch.py \
  publish_period:=0.5 stale_timeout:=3.0 topic:=/host_status
```

`publish_period` 至少为 0.1 秒；`stale_timeout` 应大于发布间隔。
无桌面环境时添加 `gui:=false`，仅启动采集节点。

也可以在两个终端分别运行，此时需分别停止：

```bash
ros2 run status_publisher sys_status_pub
ros2 run status_publisher sys_status_gui
```

## 测试

```bash
QT_QPA_PLATFORM=offscreen colcon test
colcon test-result --verbose
```
