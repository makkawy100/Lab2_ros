#!/usr/bin/env python3
"""ROS subscription and pyserial test over a pseudo-terminal. No physical board is used."""
import os,pty,select,time,json,signal,subprocess
from pathlib import Path
from process_cleanup import stop_tree
os.environ["ROS_DOMAIN_ID"]="72"
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory
from arm_control.publisher import message
from arm_control.core import TOPIC
PREFIX='humble_'
OUT=Path(__file__).resolve().parents[1]/'test_results';OUT.mkdir(exist_ok=True)
master,slave=pty.openpty();port=os.ttyname(slave)
f=(OUT/(PREFIX+'serial_pty.log')).open('w')
p=subprocess.Popen(['ros2','run','arm_hardware','serial_bridge','--ros-args','-p','dry_run:=false','-p','port:='+port],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
rclpy.init();n=Node('serial_pipeline_test');pub=n.create_publisher(JointTrajectory,TOPIC,10)
packets=[];buf=b'';report={'status':'FAIL','test':'ROS + pyserial pseudo-terminal test (no physical servos)'}
try:
 end=time.monotonic()+12
 while not pub.get_subscription_count() and time.monotonic()<end:rclpy.spin_once(n,timeout_sec=.1)
 assert pub.get_subscription_count()>0,'No serial subscriber'
 pub.publish(message([.3,-.4,.5,-.2],3.0));end=time.monotonic()+5
 while time.monotonic()<end:
  rclpy.spin_once(n,timeout_sec=.01)
  if select.select([master],[],[],0)[0]:
   buf+=os.read(master,4096)
   while b'\n' in buf:
    line,buf=buf.split(b'\n',1);packets.append(line.decode());os.write(master,b'OK\n')
 assert len(packets)>80,packets
 assert packets[-1]=='S,107,67',packets[-1]
 assert len(set(packets))>15,'No interpolation'
 assert p.poll() is None,'Bridge crashed'
 report.update(status='PASS',packet_count=len(packets),distinct_packets=len(set(packets)),first=packets[0],last=packets[-1])
finally:
 n.destroy_node();rclpy.try_shutdown();stop_tree(p)
 f.close();os.close(master);os.close(slave)
 (OUT/(PREFIX+'serial_pty.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
