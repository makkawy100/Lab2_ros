#!/usr/bin/env python3
"""Rebuild committed world from URDF using Gazebo's actual URDF->SDF converter."""
from pathlib import Path
import subprocess
import argparse
import xml.etree.ElementTree as E
args=argparse.ArgumentParser();args.add_argument('--variant',choices=['fortress'],default='fortress');variant=args.parse_args().variant
ROOT=Path(__file__).resolve().parents[1]
urdf=ROOT/'src/arm_description/urdf/arm.urdf'
result=subprocess.run(['ign' if variant=='fortress' else 'gz','sdf','-p',str(urdf)],check=True,capture_output=True,text=True)
model=E.fromstring(result.stdout).find('model')
if model is None: raise RuntimeError('gz sdf produced no model')
model.set('name','assignment_arm')
# World constraint anchors base_link without adding a fake root link in the URDF.
j=E.SubElement(model,'joint',name='mount_to_world',type='fixed')
E.SubElement(j,'parent').text='world'; E.SubElement(j,'child').text='base_link'
for n in range(1,5):
 p=E.SubElement(model,'plugin',filename='gz-sim-joint-position-controller-system',name='gz::sim::systems::JointPositionController')
 for k,v in [('joint_name',f'joint{n}'),('topic',f'/sim/joint{n}/cmd_pos'),('use_velocity_commands','true'),('cmd_max','1.5')]: E.SubElement(p,k).text=v
p=E.SubElement(model,'plugin',filename='gz-sim-joint-state-publisher-system',name='gz::sim::systems::JointStatePublisher')
E.SubElement(p,'topic').text='/arm/joint_state'; E.SubElement(p,'update_rate').text='50'
for n in range(1,5): E.SubElement(p,'joint_name').text=f'joint{n}'
sdf=E.Element('sdf',version='1.9');w=E.SubElement(sdf,'world',name='arm_world')
E.SubElement(w,'gravity').text='0 0 -9.81'
physics=E.SubElement(w,'physics',name='default',type='ignored')
E.SubElement(physics,'max_step_size').text='0.001';E.SubElement(physics,'real_time_factor').text='1.0'
for file,name in [('physics','Physics'),('user-commands','UserCommands'),('scene-broadcaster','SceneBroadcaster')]: E.SubElement(w,'plugin',filename='gz-sim-'+file+'-system',name='gz::sim::systems::'+name)
light=E.SubElement(w,'light',name='sun',type='directional')
for k,v in [('pose','0 0 5 0 0 0'),('diffuse','0.9 0.9 0.9 1'),('specular','0.3 0.3 0.3 1'),('direction','-0.5 0.2 -1'),('cast_shadows','true')]:E.SubElement(light,k).text=v
# Local ground geometry. No internet Fuel models required.
ground=E.SubElement(w,'model',name='ground');E.SubElement(ground,'static').text='true'
l=E.SubElement(ground,'link',name='ground_link')
for tag in ['visual','collision']:
 item=E.SubElement(l,tag,name='plane_'+tag);g=E.SubElement(item,'geometry');p=E.SubElement(g,'plane');E.SubElement(p,'normal').text='0 0 1';E.SubElement(p,'size').text='2 2'
 if tag=='visual':
  mat=E.SubElement(item,'material');E.SubElement(mat,'ambient').text='0.65 0.68 0.7 1';E.SubElement(mat,'diffuse').text='0.65 0.68 0.7 1'
w.append(model)
gui=E.SubElement(w,'gui',fullscreen='false')
p=E.SubElement(gui,'plugin',filename='MinimalScene',name='3D View')
for k,v in [('engine','ogre2'),('scene','scene'),('ambient_light','0.5 0.5 0.5'),('background_color','0.85 0.88 0.92'),('camera_pose','0.65 -0.7 0.55 0 0.35 2.35')]:E.SubElement(p,k).text=v
p=E.SubElement(gui,'plugin',filename='GzSceneManager',name='Scene Manager')
if variant=='fortress':
 for p in sdf.iter('plugin'):
  if p.get('filename','').startswith('gz-sim-'):
   p.set('filename',p.get('filename').replace('gz-sim-','ignition-gazebo-'))
  if p.get('name','').startswith('gz::sim::'):
   p.set('name',p.get('name').replace('gz::sim::','ignition::gazebo::'))
E.indent(sdf)
out=ROOT/'src/arm_simulation/worlds/arm_world.sdf';out=out.with_name('arm_world_fortress.sdf') if variant=='fortress' else out;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(E.tostring(sdf,encoding='unicode')+'\n')
print(out)
