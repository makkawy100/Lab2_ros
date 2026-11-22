"""Publish one multi-joint position command, waiting for subscriber discovery."""
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from .core import JOINTS, TOPIC, validate

def message(positions, seconds):
    validate(list(JOINTS), [(positions, seconds)])
    m = JointTrajectory(); m.joint_names = list(JOINTS)
    p = JointTrajectoryPoint(); p.positions = list(map(float, positions))
    ns = int(round(seconds * 1e9))
    p.time_from_start.sec, p.time_from_start.nanosec = divmod(ns, 1000000000)
    m.points = [p]
    return m

def main(args=None):
    rclpy.init(args=args); n = Node('arm_trajectory_publisher')
    n.declare_parameter('positions', [0.3, -0.4, 0.5, -0.2])
    n.declare_parameter('duration', 3.0)
    pub = n.create_publisher(JointTrajectory, TOPIC, 10)
    import time
    try:
        msg = message(n.get_parameter('positions').value, n.get_parameter('duration').value)
        deadline = time.monotonic() + 10
        while pub.get_subscription_count() == 0 and time.monotonic() < deadline:
            rclpy.spin_once(n, timeout_sec=0.1)
        if pub.get_subscription_count() == 0:
            raise RuntimeError('No subscribers. Launch simulation or hardware bridge first.')
        pub.publish(msg)
        # Allow the outgoing DDS sample to flush before destroying the writer.
        for _ in range(5): rclpy.spin_once(n, timeout_sec=0.1)
        n.get_logger().info('Published four-joint trajectory')
    finally: n.destroy_node(); rclpy.try_shutdown()
