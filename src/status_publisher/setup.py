from glob import glob

from setuptools import find_packages, setup

package_name = 'status_publisher'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml', 'LICENSE']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='System Monitor Maintainers',
    maintainer_email='maintainer@example.com',
    description='ROS 2 system status publisher and PyQt5 monitor',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'sys_status_pub = status_publisher.sys_status_pub:main',
            'sys_status_gui = status_publisher.sys_status_gui:main',
        ],
    },
)
