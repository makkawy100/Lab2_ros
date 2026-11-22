"""Interpolate JointTrajectory targets and command four Gazebo position systems."""
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import Float64
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory
from .core import Motion, JOINTS, TOPIC, from_message

class SimAdapter(Node):
    def __init__(self):
        super().__init__('arm_sim_adapter')
        self.motion = Motion()
        self.active = False
        self.last_time = 0.0
        self.pubs = [self.create_publisher(Float64, '/sim/'+j+'/cmd_pos', 10) for j in JOINTS]
        self.create_subscription(JointTrajectory, TOPIC, self.receive, 10)
        self.create_subscription(JointState, '/joint_states', self.feedback, qos_profile_sensor_data)
        self.create_timer(0.02, self.tick)

    def now_seconds(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def feedback(self, msg):
        if not self.active and all(j in msg.name for j in JOINTS):
            self.motion.current = tuple(msg.position[msg.name.index(j)] for j in JOINTS)

    def receive(self, msg):
        try:
            points = from_message(msg)
            self.motion.command(points, self.now_seconds())
        except ValueError as e:
            self.get_logger().error(str(e)); return
        self.active = True

    def tick(self):
        now = self.now_seconds()
        if now < self.last_time:
            self.motion = Motion(); self.active = False
        self.last_time = now
        for pub, position in zip(self.pubs, self.motion.sample(now)):
            pub.publish(Float64(data=position))

def main(args=None):
    rclpy.init(args=args); node = SimAdapter()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.destroy_node(); rclpy.try_shutdown()
