#!/usr/bin/env python3
import os, subprocess, time, signal
from pathlib import Path
from process_cleanup import stop_tree
VARIANT=os.environ.get('ARM_VARIANT','humble')
if VARIANT!='humble': raise SystemExit('The main branch keeps only the Humble variant. Unset ARM_VARIANT or use ARM_VARIANT=humble.')
PREFIX='humble_'
os.environ['ROS_DOMAIN_ID']='74'
os.environ['GZ_PARTITION']='arm_visual_test'
os.environ['IGN_PARTITION']='arm_visual_test'
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test_results';OUT.mkdir(exist_ok=True)
procs=[]
def start(cmd,name):
 f=(OUT/(PREFIX+name+'.log')).open('w');p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);procs.append((p,f));return p
try:
 start(['Xvfb',':95','-screen','0','1600x1000x24'],'xvfb')
 os.environ.update(DISPLAY=':95',LIBGL_ALWAYS_SOFTWARE='1',QT_X11_NO_MITSHM='1',QT_QPA_PLATFORM='xcb')
 time.sleep(1)
 start(['ros2','launch','arm_simulation','simulation_humble.launch.py'],'visual_launch')
 time.sleep(15)
 print(subprocess.run(['xdotool','search','--onlyvisible','--name','.'],capture_output=True,text=True).stdout)
 subprocess.run(['/usr/bin/python3','-c',f'from PIL import ImageGrab;ImageGrab.grab().save({str(OUT/(PREFIX+"desktop_initial.png"))!r})'])
 for title,filename in [('RViz','rviz_home.png'),('Gazebo','gazebo_home.png')]:
  result=subprocess.run(['xdotool','search','--onlyvisible','--name',title],capture_output=True,text=True)
  wins=result.stdout.split()
  for win in wins:
   subprocess.run(['xdotool','windowraise',win]);subprocess.run(['xdotool','windowmove',win,'0','0']);time.sleep(2)
   subprocess.run(['/usr/bin/python3','-c',f'from PIL import ImageGrab;ImageGrab.grab().save({str(OUT/(PREFIX+filename))!r})'])
 start(['ros2','run','arm_control','trajectory_publisher'],'visual_command')
 time.sleep(6)
 for title,filename in [('RViz','rviz_moved.png'),('Gazebo','gazebo_moved.png')]:
  result=subprocess.run(['xdotool','search','--onlyvisible','--name',title],capture_output=True,text=True)
  for win in result.stdout.split():
   subprocess.run(['xdotool','windowraise',win]);subprocess.run(['xdotool','windowmove',win,'0','0']);time.sleep(1)
   subprocess.run(['/usr/bin/python3','-c',f'from PIL import ImageGrab;ImageGrab.grab().save({str(OUT/(PREFIX+filename))!r})'])
 start(['ros2','run','arm_control','sliders'],'sliders')
 time.sleep(3)
 subprocess.run(['/usr/bin/python3','-c',f'from PIL import ImageGrab;ImageGrab.grab().save({str(OUT/(PREFIX+"sliders.png"))!r})'])
finally:
 for p,f in reversed(procs):
  stop_tree(p)
  f.close()
print('Saved actual UI screenshots to',OUT)
