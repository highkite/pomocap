import json
import bpy
from bpy import context

def print(data):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")

data = None

with open('/home/highway/Projekte/pose_detection/output2.json', 'r') as f:
    data = json.load(f)

print(data)

def create_missing_objects(keypoints):
    """Creates cubes for every node in the pose data, if it does not exists"""

    max_z = max([keypoint["position"]["y"] for keypoint in keypoints])

    for keypoint in keypoints:
        if not bpy.context.scene.objects.get(keypoint["part"]):
            print(f"Keypoint: ${keypoint['part']}")
            bpy.ops.mesh.primitive_cube_add(location=(keypoint["position"]["x"], 0, max_z - keypoint["position"]["y"]))
            ob = bpy.context.active_object
            ob.name = keypoint["part"]

def set_initial_location(keypoints):
    max_z = max([keypoint["position"]["y"] for keypoint in keypoints])

    for keypoint in keypoints:
        obj = bpy.context.scene.objects.get(keypoint["part"])

        if obj:
            obj.location.x = keypoint["position"]["x"]
            obj.location.y = 0
            obj.location.z = max_z - keypoint["position"]["y"]

def set_key_frames(keypoints, _frame):
    max_z = max([keypoint["position"]["y"] for keypoint in keypoints])

    for keypoint in keypoints:
        obj = bpy.context.scene.objects.get(keypoint["part"])

        if obj:
            obj.location.x = keypoint["position"]["x"]
            obj.location.y = 0
            obj.location.z = max_z - keypoint["position"]["y"]
            obj.keyframe_insert(data_path="location", frame=_frame, index=2)

create_missing_objects(data[0]["keypoints"])
set_initial_location(data[0]["keypoints"])

n = 0
for k in data:
    set_key_frames(k["keypoints"], n)
    n += 25
