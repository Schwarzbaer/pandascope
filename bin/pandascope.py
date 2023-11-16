import enum

#from panda3d.core import Vec2
from panda3d.core import Vec3
from direct.showbase.ShowBase import ShowBase

from keybindings.device_listener import add_device_listener
from keybindings.device_listener import SinglePlayerAssigner


class CameraControl(enum.Enum):
    MOVEMENT = 1
    ROTATION = 2
    TURNTABLE = 3


class CameraMode(enum.Enum):
    BASE = 1
    MODIFIED = 2


class AnchorMode(enum.Enum):
    RELATIVE_TO_CAMERA = 1
    STATIC = 2


camera_modes = {
    CameraMode.BASE: set([
        CameraControl.MOVEMENT,
        CameraControl.ROTATION,
        #AnchorMode.STATIC,
        AnchorMode.RELATIVE_TO_CAMERA,
    ]),
    CameraMode.MODIFIED: set([
        CameraControl.TURNTABLE,
        AnchorMode.STATIC,
    ]),
}
turntable_camera_movement_speed = Vec3(120.0, 45.0, 5.0)
turntable_camera_rotation_speed = Vec3(120.0, 120.0, 120.0)
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
    import random
    for _ in range(1000):
        m = base.loader.load_model('models/smiley')
        m.reparent_to(base.render)
        m.set_pos(
            (random.random() * 2 - 1) * 500,
            (random.random() * 2 - 1) * 500,
            (random.random() * 2 - 1) * 500,
        )


def maybe_quit(task):
    hid_state = base.device_listener.read_context('control')
    if hid_state['quit']:
        base.task_mgr.stop()
    return task.cont


def toggle_camera():
    global camera_mode
    if camera_mode == CameraMode.TURNTABLE:
        base.cam.wrt_reparent_to(base.render)
        camera_anchor.wrt_reparent_to(base.cam)
        camera_mode = CameraMode.FREEFLIGHT
    else:
        camera_anchor.wrt_reparent_to(base.render)            
        base.cam.wrt_reparent_to(camera_gimbal)
        camera_mode = CameraMode.TURNTABLE


def update_camera_movement(mode):
    hid_state = base.device_listener.read_context('camera')

    movement = Vec3(hid_state['movement'])
    movement.componentwise_mult(freeflight_camera_movement_speed)
    movement *= globalClock.dt

    if AnchorMode.STATIC in mode:
        base.cam.set_pos(base.cam, movement)
    else:  # AnchorMode.RELATIVE_TO_CAMERA
        camera_anchor.set_pos(
            camera_anchor,
            camera_anchor.get_relative_vector(base.cam, movement),
        )


def update_camera_rotation(mode):
    hid_state = base.device_listener.read_context('camera')

    rotation = Vec3(hid_state['rotation'])
    rotation.componentwise_mult(freeflight_camera_rotation_speed)
    rotation *= globalClock.dt

    if AnchorMode.STATIC in mode:
        base.cam.set_hpr(base.cam, rotation)
    else:  # AnchorMode.RELATIVE_TO_CAMERA
        base.cam.wrt_reparent_to(base.render)
        camera_anchor.wrt_reparent_to(base.cam)
        base.cam.set_hpr(base.cam, rotation)
        camera_anchor.wrt_reparent_to(base.render)
        base.cam.wrt_reparent_to(camera_gimbal)


def update_camera_turntable(mode):
    hid_state = base.device_listener.read_context('camera')

    movement = Vec3(hid_state['turntable'])
    movement.componentwise_mult(turntable_camera_movement_speed)
    movement *= globalClock.dt
    
    camera_gimbal.set_h(camera_gimbal.get_h() + movement.x)
    
    pitch = camera_gimbal.get_p() - movement.y
    pitch = min(max(pitch, -89.9), 89.9)
    camera_gimbal.set_p(pitch)
    
    zoom = base.cam.get_y() + movement.z
    zoom = min(0.1, zoom)
    base.cam.set_y(zoom)


def camera_movement(task):
    hid_state = base.device_listener.read_context('camera')

    if hid_state['modify_camera_mode']:
        mode = camera_modes[CameraMode.MODIFIED]
    else:
        mode = camera_modes[CameraMode.BASE]
    
    if CameraControl.MOVEMENT in mode:
        update_camera_movement(mode)
    if CameraControl.ROTATION in mode:
        update_camera_rotation(mode)
    if CameraControl.TURNTABLE in mode:
        update_camera_turntable(mode)

    if hid_state['rotate_camera_to_anchor']:
        base.cam.look_at(camera_anchor)
    if hid_state['rotate_anchor_to_camera']:
        base.cam.wrt_reparent_to(base.render)
        camera_anchor.set_hpr(base.cam, 0, 0, 0)
        camera_gimbal.set_hpr(0, 0, 0)
        base.cam.wrt_reparent_to(camera_gimbal)
    if hid_state['snap_anchor_to_camera']:
        base.cam.wrt_reparent_to(base.render)
        camera_anchor.set_pos(base.cam, 0, 10, 0)
        base.cam.wrt_reparent_to(camera_gimbal)
    if hid_state['snap_camera_to_anchor']:
        camera_gimbal.set_hpr(0, 0, 0)
        base.cam.set_pos(0, -10, 0)
        
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
