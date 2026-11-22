import math
import sys
import unittest
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/arm_control'))
from arm_control.core import Motion,validate,servo_angle,encode,JOINTS

class TrajectoryTests(unittest.TestCase):
    def test_order(self):
        names=list(reversed(JOINTS))
        self.assertEqual(validate(names,[([.4,.3,.2,.1],2)])[0][0],(.1,.2,.3,.4))
    def test_reject_bad_names(self):
        for names in [[],['joint1']*4,['a','b','c','d']]:
            with self.subTest(names=names),self.assertRaises(ValueError):validate(names,[([0.]*4,2)])
    def test_reject_positions(self):
        for values in [[],[0]*3,[math.nan]*4,[math.inf]*4,[2.]*4]:
            with self.subTest(values=values),self.assertRaises(ValueError):validate(list(JOINTS),[(values,2)])
    def test_reject_time(self):
        for t in [0,-1,math.nan,math.inf]:
            with self.subTest(t=t),self.assertRaises(ValueError):validate(list(JOINTS),[([0]*4,t)])
    def test_empty(self):
        with self.assertRaises(ValueError):validate(list(JOINTS),[])
    def test_nonmonotonic(self):
        with self.assertRaises(ValueError):validate(list(JOINTS),[([0]*4,2),([0]*4,1)])
    def test_interpolation(self):
        m=Motion();m.command([((1.,)*4,2)],10)
        self.assertEqual(m.sample(9),(0.,)*4)
        self.assertEqual(m.sample(11),(.5,)*4)
        self.assertEqual(m.sample(12),(1.,)*4)
        self.assertEqual(m.sample(20),(1.,)*4)
    def test_multi_point(self):
        m=Motion();m.command([((1.,)*4,2),((0.,)*4,4)],0)
        self.assertEqual(m.sample(3),(.5,)*4)
    def test_preemption_continuity(self):
        m=Motion();m.command([((1.,)*4,2)],0);m.command([((0.,)*4,2)],1)
        self.assertEqual(m.sample(1),(.5,)*4)
        self.assertEqual(m.sample(2),(.25,)*4)
    def test_speed_limit(self):
        m=Motion()
        with self.assertRaises(ValueError):m.command([((1.,)*4,.1)],0)
    def test_servo_mapping(self):
        self.assertEqual([servo_angle(x) for x in [-math.pi/2,0,math.pi/2]],[0,90,180])
    def test_clamp(self):
        self.assertEqual(servo_angle(50),180);self.assertEqual(servo_angle(-50),0)
    def test_calibration(self):
        self.assertEqual(servo_angle(math.pi/6,80,-1),50)
    def test_invalid_calibration(self):
        for args in [(math.nan,90,1),(0,90,0),(0,math.inf,1)]:
            with self.subTest(args=args),self.assertRaises(ValueError):servo_angle(*args)
    def test_wire(self):
        self.assertEqual(encode([math.pi/2,-math.pi/2,0,0]),b'S,180,0\n')

class DescriptionTests(unittest.TestCase):
    def setUp(self):
        self.root=E.parse(ROOT/'src/arm_description/urdf/arm.urdf').getroot()
    def test_four_revolute_joints(self):
        self.assertEqual([j.get('name') for j in self.root.findall("joint[@type='revolute']")],list(JOINTS))
    def test_all_link_properties(self):
        for l in self.root.findall('link'):
            for tag in ['visual/geometry','collision/geometry','inertial/mass','inertial/inertia']:
                self.assertIsNotNone(l.find(tag),(l.get('name'),tag))
            self.assertGreater(float(l.find('inertial/mass').get('value')),0)
            inertia=l.find('inertial/inertia')
            for term in ['ixx','iyy','izz']:self.assertGreater(float(inertia.get(term)),0)
    def test_dimensions(self):
        self.assertEqual(float(self.root.find("link[@name='base_link']/visual/geometry/cylinder").get('length')),.08)
        for name,index,expected in [('L1',2,.12),('L2',0,.15),('L3',0,.09),('end_effector',0,.06)]:
            actual=self.root.find(f"link[@name='{name}']/visual/geometry/box").get('size')
            self.assertEqual(float(actual.split()[index]),expected)
    def test_chain(self):
        joints=self.root.findall('joint');children={j.find('child').get('link') for j in joints}
        self.assertEqual({l.get('name') for l in self.root.findall('link')}-children,{'base_link'})
        self.assertEqual(len(children),4)
    def test_world(self):
        w=E.parse(ROOT/'src/arm_simulation/worlds/arm_world_fortress.sdf').getroot().find('world')
        arm=w.find("model[@name='assignment_arm']")
        self.assertEqual(arm.find("joint[@name='mount_to_world']/parent").text,'world')
        for j in JOINTS:self.assertIsNotNone(arm.find(f"joint[@name='{j}']"))
        self.assertEqual(len(arm.findall("plugin[@name='ignition::gazebo::systems::JointPositionController']")),4)

if __name__=='__main__':unittest.main(verbosity=2)
