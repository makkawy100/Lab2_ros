#!/usr/bin/env python3
"""Live ROS/Gazebo smoke test. Requires a built, sourced workspace."""
import os
import uuid
os.environ["GZ_PARTITION"]="arm_test_"+uuid.uuid4().hex
os.environ["ROS_DOMAIN_ID"]="71"
import json
import math
import time
import signal
import subprocess
from pathlib import Path
from process_cleanup import stop_tree
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState
from tf2_msgs.msg import TFMessage
from trajectory_msgs.msg import JointTrajectory
from arm_control.publisher import message
from arm_control.core import TOPIC, JOINTS
ROOT=Path(__file__).resolve().parents[1]
VARIANT=os.environ.get('ARM_VARIANT','jazzy')
PREFIX='humble_' if VARIANT=='humble' else ''
os.environ['IGN_PARTITION']=os.environ['GZ_PARTITION']
OUT=ROOT/'test_results';OUT.mkdir(exist_ok=True)

def main():
    log=(OUT/(PREFIX+'live_simulation.log')).open('w')
    launch=subprocess.Popen(['ros2','launch','arm_simulation','simulation_humble.launch.py' if VARIANT=='humble' else 'simulation.launch.py','headless:=true','rviz:=false','hardware:=true','dry_run:=true'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    rclpy.init(); n=Node('assignment_smoke_test')
    states=[]; transforms=set()
    n.create_subscription(JointState,'/joint_states',lambda m: states.append((time.monotonic(),dict(zip(m.name,m.position)))),qos_profile_sensor_data)
    n.create_subscription(TFMessage,'/tf',lambda m: transforms.update(t.child_frame_id for t in m.transforms),10)
    pub=n.create_publisher(JointTrajectory,TOPIC,10)
    report={'test':'Real ROS 2 '+VARIANT+' + Gazebo headless motion, not mocked','status':'FAIL'}
    try:
        end=time.monotonic()+45
        while (not states or pub.get_subscription_count()<2) and time.monotonic()<end:
            rclpy.spin_once(n,timeout_sec=0.1)
        assert states, 'No actual Gazebo joint feedback'
        baseline=states[-1][1]
        target=[0.3,-0.4,0.5,-0.2]
        pub.publish(message(target,3.0)); sent=time.monotonic()
        while time.monotonic()-sent<6:
            rclpy.spin_once(n,timeout_sec=0.02)
        final=states[-1][1]
        error={j:abs(final[j]-target[i]) for i,j in enumerate(JOINTS)}
        changed={j:abs(final[j]-baseline[j]) for j in JOINTS}
        assert max(error.values())<0.04, f'Target not reached: {error}'
        assert all(v>0.1 for v in changed.values()), f'No movement: {changed}'
        assert set(('L1','L2','L3','end_effector'))<=transforms, f'Missing TF: {transforms}'
        # A second command tests ongoing control, not a lucky static pose.
        pub.publish(message([0.,0.,0.,0.],2.0)); sent=time.monotonic()
        while time.monotonic()-sent<4:rclpy.spin_once(n,timeout_sec=0.02)
        home=states[-1][1]
        assert max(abs(home[j]) for j in JOINTS)<0.04, f'Home not reached: {home}'
        report.update(status='PASS',initial=baseline,target=target,final=final,absolute_error_rad=error,home=home,feedback_samples=len(states),tf_children=sorted(transforms),trajectory_subscribers=pub.get_subscription_count())
    finally:
        n.destroy_node();rclpy.try_shutdown()
        stop_tree(launch)
        log.close()
        (OUT/(PREFIX+'live_simulation.json')).write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
if __name__=='__main__':main()
