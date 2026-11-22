#!/usr/bin/env python3
"""Test the real Tk slider/button callback against real ROS/Gazebo feedback."""
import os,subprocess,time,signal,json,uuid
from pathlib import Path
from process_cleanup import stop_tree
os.environ['GZ_PARTITION']='arm_gui_'+uuid.uuid4().hex
os.environ['ROS_DOMAIN_ID']='73'
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory
from arm_control.core import TOPIC
VARIANT=os.environ.get('ARM_VARIANT','humble')
if VARIANT!='humble': raise SystemExit('The main branch keeps only the Humble variant. Unset ARM_VARIANT or use ARM_VARIANT=humble.')
PREFIX='humble_'
os.environ['IGN_PARTITION']=os.environ['GZ_PARTITION']
OUT=Path(__file__).resolve().parents[1]/'test_results';OUT.mkdir(exist_ok=True)
procs=[]
def start(cmd,name):
 f=(OUT/(PREFIX+name+'.log')).open('w');p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);procs.append((p,f));return p
report={'status':'FAIL','test':'Real Tk slider/button callback -> ROS JointTrajectory -> actual Gazebo feedback'}
rclpy.init();n=Node('gui_smoke_test');commands=[];states=[]
n.create_subscription(JointTrajectory,TOPIC,lambda m:commands.append(m),10)
n.create_subscription(JointState,'/joint_states',lambda m:states.append(dict(zip(m.name,m.position))),qos_profile_sensor_data)
root=None
try:
 start(['Xvfb',':96','-screen','0','1200x900x24'],'gui_xvfb');time.sleep(1)
 os.environ.update(DISPLAY=':96',LIBGL_ALWAYS_SOFTWARE='1',QT_QPA_PLATFORM='xcb')
 start(['ros2','launch','arm_simulation','simulation_humble.launch.py','headless:=true','rviz:=false'],'gui_sim')
 import tkinter as tk
 from arm_control.sliders import SliderWindow
 root=tk.Tk(); ui=SliderWindow(root,n);root.update()
 end=time.monotonic()+30
 while (not states or ui.pub.get_subscription_count()<2) and time.monotonic()<end:
  rclpy.spin_once(n,timeout_sec=.1);root.update()
 assert states,'No Gazebo feedback'
 ui.sliders[0].set(30);ui.sliders[1].set(-20);ui.duration.set(3)
 root.update();ui.send_button.invoke()
 end=time.monotonic()+6
 while time.monotonic()<end:
  rclpy.spin_once(n,timeout_sec=.02);root.update()
 assert commands,'GUI did not publish a trajectory'
 targets=commands[-1].points[0].positions
 assert abs(targets[0]-.5235987756)<1e-8,targets
 actual=states[-1]
 assert abs(actual['joint1']-targets[0])<.04,(actual,targets)
 assert abs(actual['joint2']-targets[1])<.04,(actual,targets)
 report.update(status='PASS',gui_targets_rad=list(targets),actual_gazebo=actual,command_count=len(commands))
finally:
 if root:root.destroy()
 n.destroy_node();rclpy.try_shutdown()
 for p,f in reversed(procs):
  stop_tree(p)
  f.close()
 (OUT/(PREFIX+'gui_pipeline.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
