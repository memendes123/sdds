"""HeatSeeker Pro plugin example for RLBot.

Focused on reliable defensive positioning and strong clears for Heatseeker mode.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState


FIELD_HALF_WIDTH = 4096.0
FIELD_HALF_LENGTH = 5120.0
MAX_CAR_SPEED = 2300.0


@dataclass
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, value: float) -> "Vec3":
        return Vec3(self.x * value, self.y * value, self.z * value)

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def flat_length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalized(self) -> "Vec3":
        size = self.length()
        if size <= 1e-6:
            return Vec3(0.0, 0.0, 0.0)
        return Vec3(self.x / size, self.y / size, self.z / size)


class plugin_heatseeker_pro(BaseAgent):
    """Professional baseline plugin for Heatseeker.

    Strategy:
    1) Keep a disciplined defensive line between own goal and ball trajectory.
    2) Challenge only when interception window is favorable.
    3) Recover quickly to goal center after touches.
    """

    # Tunables
    DEFENSIVE_DEPTH = 900.0
    INTERCEPT_LOOKAHEAD_MIN = 0.35
    INTERCEPT_LOOKAHEAD_MAX = 1.50
    CHALLENGE_DISTANCE = 1200.0
    JUMP_STRIKE_HEIGHT = 240.0

    def initialize_agent(self) -> None:
        self.controller = SimpleControllerState()

    def get_output(self, packet):
        car = packet.game_cars[self.index]
        ball = packet.game_ball

        car_pos = Vec3(car.physics.location.x, car.physics.location.y, car.physics.location.z)
        ball_pos = Vec3(ball.physics.location.x, ball.physics.location.y, ball.physics.location.z)
        ball_vel = Vec3(ball.physics.velocity.x, ball.physics.velocity.y, ball.physics.velocity.z)

        own_goal = self._goal_center(team=self.team)
        target = self._defensive_target(ball_pos, ball_vel, own_goal)

        # Switch to active challenge when the ball is close enough to engage.
        flat_dist_to_ball = (ball_pos - car_pos).flat_length()
        if flat_dist_to_ball < self.CHALLENGE_DISTANCE:
            target = self._intercept_target(car_pos, ball_pos, ball_vel)

        controls = self._drive_to_target(car, car_pos, target)
        controls.jump = self._should_jump_strike(car_pos, ball_pos, flat_dist_to_ball)

        # Avoid random handbrake turns; only use for large angle corrections.
        yaw_error = abs(self._angle_to_target(car, car_pos, target))
        controls.handbrake = yaw_error > 1.9 and car.physics.velocity.x * car.physics.velocity.x + car.physics.velocity.y * car.physics.velocity.y > 500000

        return controls

    def _goal_center(self, team: int) -> Vec3:
        # Blue team defends negative Y, orange team defends positive Y.
        goal_y = -FIELD_HALF_LENGTH if team == 0 else FIELD_HALF_LENGTH
        return Vec3(0.0, goal_y, 0.0)

    def _defensive_target(self, ball_pos: Vec3, ball_vel: Vec3, own_goal: Vec3) -> Vec3:
        # Estimate where the Heatseeker curve will be soon (linear approximation baseline).
        speed = ball_vel.length()
        lookahead = self._clamp(speed / 2500.0, self.INTERCEPT_LOOKAHEAD_MIN, self.INTERCEPT_LOOKAHEAD_MAX)
        future_ball = ball_pos + ball_vel * lookahead

        # Stay behind the ball relative to own goal to avoid overcommits.
        to_goal = (own_goal - future_ball).normalized()
        raw_target = future_ball + to_goal * self.DEFENSIVE_DEPTH

        return Vec3(
            self._clamp(raw_target.x, -FIELD_HALF_WIDTH + 250.0, FIELD_HALF_WIDTH - 250.0),
            self._clamp(raw_target.y, -FIELD_HALF_LENGTH + 450.0, FIELD_HALF_LENGTH - 450.0),
            0.0,
        )

    def _intercept_target(self, car_pos: Vec3, ball_pos: Vec3, ball_vel: Vec3) -> Vec3:
        # Compute a practical interception point: where ball should be after travel time.
        dist = max((ball_pos - car_pos).flat_length(), 1.0)
        eta = self._clamp(dist / (MAX_CAR_SPEED * 0.9), 0.10, 1.30)
        predicted = ball_pos + ball_vel * eta
        return Vec3(predicted.x, predicted.y, 0.0)

    def _drive_to_target(self, car, car_pos: Vec3, target: Vec3) -> SimpleControllerState:
        controls = SimpleControllerState()
        angle = self._angle_to_target(car, car_pos, target)
        distance = (target - car_pos).flat_length()

        controls.steer = self._clamp(angle * 3.0, -1.0, 1.0)
        controls.throttle = 1.0 if distance > 250.0 else 0.2

        # Conservative boost usage: only when mostly aligned.
        controls.boost = distance > 1400.0 and abs(angle) < 0.18 and car.boost > 5

        # Small brake when target is behind to rotate faster.
        if abs(angle) > 2.2:
            controls.throttle = -0.4
            controls.boost = False

        return controls

    def _should_jump_strike(self, car_pos: Vec3, ball_pos: Vec3, flat_dist_to_ball: float) -> bool:
        return (
            flat_dist_to_ball < 260.0
            and self.JUMP_STRIKE_HEIGHT < ball_pos.z < 500.0
            and car_pos.z < 40.0
        )

    @staticmethod
    def _angle_to_target(car, car_pos: Vec3, target: Vec3) -> float:
        car_yaw = car.physics.rotation.yaw
        car_forward = Vec3(math.cos(car_yaw), math.sin(car_yaw), 0.0)

        to_target = (target - car_pos).normalized()
        dot = car_forward.x * to_target.x + car_forward.y * to_target.y
        det = car_forward.x * to_target.y - car_forward.y * to_target.x
        return math.atan2(det, dot)

    @staticmethod
    def _clamp(value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(maximum, value))
