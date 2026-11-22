"""Pure Python trajectory validation, sampling and servo encoding. No ROS needed."""
import math
JOINTS = ('joint1', 'joint2', 'joint3', 'joint4')
LIMIT = math.pi / 2
TOPIC = '/arm_controller/joint_trajectory'

def validate(names, points):
    """Accept complete commands only; reject unknown/duplicate joints and NaNs."""
    if len(names) != 4 or set(names) != set(JOINTS):
        raise ValueError('Provide joint1..joint4 exactly once')
    if not points:
        raise ValueError('At least one point is required')
    out, last = [], 0.0
    for positions, seconds in points:
        if len(positions) != 4 or not all(math.isfinite(p) for p in positions):
            raise ValueError('Four finite positions required')
        if any(abs(p) > LIMIT + 1e-9 for p in positions):
            raise ValueError('Position outside [-pi/2, pi/2]')
        if not math.isfinite(seconds) or seconds <= last:
            raise ValueError('Times must be positive and strictly increasing')
        out.append((tuple(positions[names.index(j)] for j in JOINTS), seconds))
        last = seconds
    return out

def from_message(msg):
    if msg.header.stamp.sec or msg.header.stamp.nanosec:
        raise ValueError('Only immediate trajectories (zero header stamp) supported')
    for p in msg.points:
        if p.velocities or p.accelerations or p.effort:
            raise ValueError('Positions-only trajectories required')
        if p.time_from_start.sec < 0 or not 0 <= p.time_from_start.nanosec < 1000000000:
            raise ValueError('Invalid duration')
    return validate(list(msg.joint_names), [(list(p.positions), p.time_from_start.sec + p.time_from_start.nanosec * 1e-9) for p in msg.points])

class Motion:
    def __init__(self):
        self.current = (0.0,) * 4
        self.initial = self.current
        self.points = []
        self.start = 0.0

    def command(self, points, now):
        self.sample(now)
        previous, t0 = self.current, 0.0
        for target, t1 in points:
            if any(abs(b-a)/(t1-t0) > 1.5 + 1e-6 for a,b in zip(previous,target)):
                raise ValueError('Requested speed exceeds 1.5 rad/s; increase duration')
            previous, t0 = target, t1
        self.initial, self.points, self.start = self.current, points, now

    def sample(self, now):
        if not self.points:
            return self.current
        elapsed = max(0.0, now - self.start)
        previous, t0 = self.initial, 0.0
        for target, t1 in self.points:
            if elapsed <= t1:
                u = (elapsed - t0) / (t1 - t0)
                self.current = tuple(a + (b-a)*u for a,b in zip(previous, target))
                return self.current
            previous, t0 = target, t1
        self.current = self.points[-1][0]
        return self.current

def servo_angle(radians, offset=90.0, direction=1.0):
    if not all(math.isfinite(v) for v in (radians, offset, direction)) or direction not in (-1.0, 1.0):
        raise ValueError('Invalid servo calibration')
    return max(0, min(180, int(math.floor(offset + direction * math.degrees(radians) + 0.5))))

def encode(positions, offsets=(90.,90.), directions=(1.,1.)):
    # Only joint1 and joint2 are wired in the minimum two-servo build.
    a,b = [servo_angle(positions[i], offsets[i], directions[i]) for i in range(2)]
    return f'S,{a},{b}\n'.encode('ascii')
