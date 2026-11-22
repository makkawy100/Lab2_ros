"""Manual assignment demo tool. Move sliders, then press Send trajectory."""
import math
import tkinter as tk
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory
from .core import JOINTS, TOPIC
from .publisher import message

class SliderWindow:
    def __init__(self, root, node):
        self.root, self.node = root, node
        self.pub = node.create_publisher(JointTrajectory, TOPIC, 10)
        root.title('ROS 2 Arm | Trajectory Sliders')
        tk.Label(root, text='Angles in degrees. Check servo clearance before sending.').pack(padx=18,pady=12)
        self.sliders=[]
        for name in JOINTS:
            s=tk.Scale(root, label=name, from_=-90, to=90, orient=tk.HORIZONTAL, length=430)
            s.pack(padx=18); self.sliders.append(s)
        self.duration=tk.Scale(root,label='Duration (seconds)',from_=1,to=10,resolution=0.5,orient=tk.HORIZONTAL,length=430)
        self.duration.set(3); self.duration.pack(padx=18)
        self.status=tk.StringVar(value='Start simulation first. Hardware is opt-in.')
        self.send_button=tk.Button(root,text='Send trajectory',command=self.send)
        self.send_button.pack(pady=10)
        tk.Label(root,textvariable=self.status,wraplength=440).pack(pady=8)

    def send(self):
        if not self.pub.get_subscription_count():
            self.status.set('No subscribers. Start simulation or hardware first.'); return
        self.pub.publish(message([math.radians(s.get()) for s in self.sliders], self.duration.get()))
        self.status.set('Sent to '+TOPIC)

def main(args=None):
    rclpy.init(args=args); n=Node('arm_sliders'); root=tk.Tk(); SliderWindow(root,n)
    def spin():
        rclpy.spin_once(n,timeout_sec=0); root.after(20,spin)
    root.after(20,spin)
    try: root.mainloop()
    finally: n.destroy_node(); rclpy.try_shutdown()
