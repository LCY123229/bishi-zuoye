from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, Shutdown
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    topic = LaunchConfiguration('topic')
    publisher = Node(
        package='status_publisher', executable='sys_status_pub', output='screen',
        parameters=[{'publish_period': ParameterValue(
            LaunchConfiguration('publish_period'), value_type=float)}],
        remappings=[('system_status', topic)],
        on_exit=[Shutdown(reason='Publisher exited')],
    )
    gui = Node(
        package='status_publisher', executable='sys_status_gui', output='screen',
        condition=IfCondition(LaunchConfiguration('gui')),
        parameters=[{'stale_timeout': ParameterValue(
            LaunchConfiguration('stale_timeout'), value_type=float)}],
        remappings=[('system_status', topic)],
        on_exit=[Shutdown(reason='Monitor window closed')],
    )
    return LaunchDescription([
        DeclareLaunchArgument('publish_period', default_value='1.0'),
        DeclareLaunchArgument('stale_timeout', default_value='3.0'),
        DeclareLaunchArgument('topic', default_value='system_status'),
        DeclareLaunchArgument('gui', default_value='true'),
        publisher,
        gui,
    ])
