import enum

from panda3d.core import Vec2
from panda3d.core import Vec3
from direct.showbase.ShowBase import ShowBase

from keybindings.device_listener import add_device_listener
from keybindings.device_listener import SinglePlayerAssigner


class CameraMode(enum.Enum):
    FREEFLIGHT = 1
    TURNTABLE = 2


camera_mode = CameraMode.TURNTABLE
turntable_camera_speed = Vec2(120.0, 45.0)
freeflight_camera_movement_speed = Vec3(10.0, 10.0, 10.0)
freeflight_camera_rotation_speed = Vec3(120.0, 120.0, 120.0)

camera_anchor = None
camera_gimbal = None


def setup_scene():
    global camera_anchor
    global camera_gimbal
    # Turntable hierarchy
    camera_anchor = base.render.attach_new_node('camera_anchor')
    camera_gimbal = camera_anchor.attach_new_node('camera_gimbal')
    base.cam.reparent_to(camera_gimbal)
    base.cam.set_pos(0, -10, 0)
    m = base.loader.load_model('models/zup-axis')
    m.reparent_to(camera_anchor)
    m.set_scale(0.1)

    # Specific setup; Modularize this away.
    m = base.loader.load_model('models/smiley')
    m.reparent_to(base.render)
    # import random
    # for _ in range(1000):
    #     m = base.loader.load_model('models/smiley')
    #     m.reparent_to(base.render)
    #     m.set_pos(
    #         (random.random() * 2 - 1) * 500,
    #         (random.random() * 2 - 1) * 500,
    #         (random.random() * 2 - 1) * 500,
    #     )


def maybe_quit(task):
    hid_state = base.device_listener.read_context('control')
    if hid_state['quit']:
        base.task_mgr.stop()
    return task.cont


def update_turntable_camera():
    hid_state = base.device_listener.read_context('turntable_camera')
    movement = Vec2(hid_state['movement'])
    movement.componentwise_mult(turntable_camera_speed)
    movement *= globalClock.dt

    old_h = camera_gimbal.get_h()
    delta_h = movement.x
    new_h = old_h + delta_h
    camera_gimbal.set_h(new_h)

    old_p = camera_gimbal.get_p()
    delta_p = movement.y
    new_p = old_p - delta_p
    clipped_p = min(max(new_p, -89.9), 89.9)
    camera_gimbal.set_p(clipped_p)


def update_freeflight_camera():
    hid_state = base.device_listener.read_context('freeflight_camera')

    movement = Vec3(hid_state['movement'])
    movement.componentwise_mult(freeflight_camera_movement_speed)
    movement *= globalClock.dt

    rotation = Vec3(hid_state['rotation'])
    rotation.componentwise_mult(freeflight_camera_rotation_speed)
    rotation *= globalClock.dt

    base.cam.set_pos(base.cam, movement)
    base.cam.set_hpr(base.cam, rotation)


def camera_movement(task):
    global camera_mode
    hid_state = base.device_listener.read_context('control')

    if hid_state['toggle_camera']:
        if camera_mode == CameraMode.TURNTABLE:
            base.cam.wrt_reparent_to(base.render)
            camera_anchor.wrt_reparent_to(base.cam)
            camera_mode = CameraMode.FREEFLIGHT
        else:
            camera_anchor.wrt_reparent_to(base.render)            
            base.cam.wrt_reparent_to(camera_gimbal)
            camera_mode = CameraMode.TURNTABLE

    if camera_mode == CameraMode.TURNTABLE:
        update_turntable_camera()
    else:
        update_freeflight_camera()

    return task.cont


if __name__ == '__main__':
    ShowBase()
    base.disable_mouse()
    add_device_listener(
        assigner=SinglePlayerAssigner(),
    )
    base.task_mgr.add(maybe_quit)
    base.task_mgr.add(camera_movement)
    setup_scene()
    base.run()
