from pathlib import Path
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    current = os.environ.get('ROS_DISTRO', '')
    if current and current != 'jazzy':
        raise RuntimeError('This launch is for jazzy. Source the matching ROS distro and use its matching project launch.')
    sim=Path(get_package_share_directory('arm_simulation'))
    desc=Path(get_package_share_directory('arm_description'))
    gz=Path(get_package_share_directory('ros_gz_sim'))
    headless=LaunchConfiguration('headless')
    return LaunchDescription([
        DeclareLaunchArgument('headless',default_value='false'),
        DeclareLaunchArgument('rviz',default_value='true'),
        DeclareLaunchArgument('hardware',default_value='false'),
        DeclareLaunchArgument('port',default_value='/dev/ttyACM0'),
        DeclareLaunchArgument('dry_run',default_value='true'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(gz/'launch/gz_sim.launch.py')),
            launch_arguments={'gz_args':PythonExpression(["'-r -s ",str(sim/'worlds/arm_world.sdf'),"' if '",headless,"' == 'true' else '-r ",str(sim/'worlds/arm_world.sdf'),"'"])}.items()),
        Node(package='ros_gz_bridge',executable='parameter_bridge',parameters=[{'config_file':str(sim/'config/bridge.yaml')}],output='screen'),
        Node(package='robot_state_publisher',executable='robot_state_publisher',parameters=[{'robot_description':(desc/'urdf/arm.urdf').read_text(),'use_sim_time':True}],output='screen'),
        Node(package='arm_control',executable='sim_adapter',parameters=[{'use_sim_time':True}],output='screen'),
        Node(package='rviz2',executable='rviz2',arguments=['-d',str(desc/'rviz/arm.rviz')],parameters=[{'use_sim_time':True}],condition=IfCondition(LaunchConfiguration('rviz')),output='screen'),
        Node(package='arm_hardware',executable='serial_bridge',parameters=[{'use_sim_time':True,'port':LaunchConfiguration('port'),'dry_run':LaunchConfiguration('dry_run')}],condition=IfCondition(LaunchConfiguration('hardware')),output='screen'),
    ])
