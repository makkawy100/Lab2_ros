"""Same trajectory topic, interpolated to two Arduino servo commands over USB."""
import time
import serial
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory
from arm_control.core import Motion, TOPIC, from_message, encode

class SerialBridge(Node):
    def __init__(self):
        super().__init__('arm_serial_bridge')
        for k,v in [('port','/dev/ttyACM0'),('baud',115200),('dry_run',True),
                    ('offsets',[90.0,90.0]),('directions',[1.0,1.0])]:
            self.declare_parameter(k,v)
        self.offsets = self.get_parameter('offsets').value
        self.directions = self.get_parameter('directions').value
        if len(self.offsets)!=2 or len(self.directions)!=2:
            raise ValueError('Exactly two offsets/directions required')
        encode((0.,)*4, self.offsets, self.directions)
        self.serial = None; self.failed = False; self.active = False
        if not self.get_parameter('dry_run').value:
            self.serial = serial.Serial(self.get_parameter('port').value,
                                        self.get_parameter('baud').value,
                                        timeout=0, write_timeout=0.2)
            time.sleep(2.0)  # Arduino resets on opening USB. No queued commands yet.
            self.serial.reset_input_buffer()
        self.motion = Motion(); self.last_packet = None; self.last_log = 0.0; self.last_time = 0.0
        self.create_subscription(JointTrajectory, TOPIC, self.receive, 10)
        self.create_timer(0.02, self.tick)
        self.get_logger().info('DRY RUN, no serial writes' if self.serial is None else 'Serial ready; awaiting trajectory')

    def now_seconds(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def receive(self, msg):
        if self.failed: return
        try:
            points = from_message(msg)
            self.motion.command(points, self.now_seconds())
        except ValueError as e:
            self.get_logger().error(str(e)); return
        self.active = True

    def tick(self):
        now = self.now_seconds()
        if now < self.last_time:
            self.active = False; self.motion = Motion()
            self.get_logger().warning('Clock reset; send a new trajectory after checking hardware')
        self.last_time = now
        if not self.active or self.failed: return
        packet = encode(self.motion.sample(now), self.offsets, self.directions)
        try:
            if self.serial:
                self.serial.write(packet)
                # Drain acknowledgements so the Arduino never blocks on a full TX buffer.
                if self.serial.in_waiting: self.serial.read(self.serial.in_waiting)
            elif packet != self.last_packet and time.monotonic()-self.last_log > 0.2:
                self.get_logger().info('TX dry-run: '+packet.decode().strip())
                self.last_log=time.monotonic()
            self.last_packet = packet
        except (serial.SerialException, serial.SerialTimeoutException, OSError) as e:
            self.failed = True
            self.get_logger().error('Serial failed; restart bridge after checking wiring: '+str(e))

    def destroy_node(self):
        if self.serial: self.serial.close()
        return super().destroy_node()

def main(args=None):
    rclpy.init(args=args); node = None
    try: node = SerialBridge(); rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        if node: node.destroy_node()
        rclpy.try_shutdown()
