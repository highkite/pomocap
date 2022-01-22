"""
Copyright (C) 2022 Thomas Osterland
highway.ita07@web.de

Created by Thomas Osterland

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

bl_info = {
    "name": "Program Walk Cycle",
    "author": "highway.ita07@web.de",
    "blender": (2, 80, 0),
    "description": "Implement walk cycle from scientific paper https://www.biomotionlab.ca/Text/trojeChapter07b.pdf",
    "version": (0, 0, 1),
    "location": "View3D",
    "warning": "This addon is still in development.",
    "wiki_url": "https://github.com/highkite",
    "category": "Object",
}

import bpy
from bpy.props import PointerProperty, StringProperty
from .walker_logic import WalkerModel


class WalkerAddonPreferences(bpy.types.AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __package__

    data_file_path: StringProperty(
        name="Data File path",
        subtype="DIR_PATH",
        default="~/.config/blender/3.0/scripts/addons/walker_addon/data.json",
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Configuration of the walker plugin")
        col = layout.column()
        col.prop(self, "data_file_path")


def remove_objects_by_name(names):
    objs = bpy.data.objects
    for name in names:
        obj = bpy.context.scene.objects.get(name)

        if obj is not None:
            objs.remove(obj, do_unlink=True)


def create_missing_objects(keypoints):
    """Creates cubes for every node in the pose data, if it does not exists"""

    user_scale = bpy.context.scene.bio_walk_scale
    scale = 1 / 20 * user_scale
    print(f"Scale: {scale}")
    for keypoint in keypoints:
        if not bpy.context.scene.objects.get(keypoint["part"]):
            bpy.ops.mesh.primitive_cube_add(
                location=(
                    keypoint["x"] * scale,
                    keypoint["z"] * scale,
                    keypoint["y"] * scale,
                )
            )
            ob = bpy.context.active_object
            ob.name = keypoint["part"]


def set_key_frames(keypoints, _frame):
    user_scale = bpy.context.scene.bio_walk_scale
    scale = 1 / 20 * user_scale

    for index in range(len(keypoints)):
        keypoint = keypoints[index]
        obj = bpy.context.scene.objects.get(keypoint["part"])

        if obj:
            obj.location.x = scale * keypoint["x"]
            obj.location.y = scale * keypoint["z"]
            obj.location.z = scale * keypoint["y"]
            obj.keyframe_insert(data_path="location", frame=_frame, index=-1)


class GenerateWalker(bpy.types.Operator):
    bl_idname = "scene.bio_walk_generate_walker"
    bl_label = "Reset Walker"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        data_file = f"{addon_prefs.data_file_path}/data.json"
        wm = WalkerModel(data_file_path=data_file)

        speed = bpy.context.scene.bio_walk_speed
        gender = bpy.context.scene.bio_walk_gender
        weight = bpy.context.scene.bio_walk_weight
        nervousness = bpy.context.scene.bio_walk_nervousness
        happiness = bpy.context.scene.bio_walk_happiness

        print(
            f"Speed: {speed}\nGender: {gender}\nWeight: {weight}\nNervousness: {nervousness}\nHappiness: {happiness}"
        )

        wm.configure_model(
            walker_gender=gender,
            walker_weight=weight,
            walker_nervousness=nervousness,
            walker_happiness=happiness,
            walker_speed=speed,
        )

        frame_start = bpy.context.scene.bio_start
        frame_end = bpy.context.scene.bio_end
        resolution = bpy.context.scene.bio_key_frame_resolution
        fps = bpy.context.scene.render.fps

        time_delta = 1000 / fps * resolution
        curtime = 1

        first = True

        for frame in range(frame_start, frame_end + 1, resolution):
            walkertime = (curtime / 159.1549) * (120 / (wm.getFrequency()))
            value = wm.derive_pose_coordinates(walkertime)
            if first:
                remove_objects_by_name([x["part"] for x in value])
                create_missing_objects(value)
                first = False
            set_key_frames(value, frame)

            curtime += time_delta

        return {"FINISHED"}


class ResetWalker(bpy.types.Operator):
    bl_idname = "scene.bio_walk_reset_walker"
    bl_label = "Reset Walker"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        data_file = f"{addon_prefs.data_file_path}/data.json"
        wm = WalkerModel(data_file_path=data_file)
        value = wm.derive_pose_coordinates(1)
        remove_objects_by_name([x["part"] for x in value])
        create_missing_objects(value)

        return {"FINISHED"}


class WalkCyclePanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_walk_cycle"
    bl_label = "Walk Cycle Panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        self.layout.label(text="Walk Cycle")
        scene = context.scene
        layout = self.layout
        col = layout.column()
        col.prop(scene, "bio_walk_scale", text="scale")
        col.prop(scene, "bio_walk_speed", text="speed")
        col.prop(scene, "bio_start", text="start")
        col.prop(scene, "bio_end", text="end")
        col.prop(scene, "bio_key_frame_resolution", text="resolution")

        col.label(text="Walk Properties")
        col.label(text="Male -- Female")
        col.prop(scene, "bio_walk_gender", slider=True, text="gender")
        col.label(text="Heavy -- Light")
        col.prop(scene, "bio_walk_weight", slider=True, text="weight")
        col.label(text="Nervous -- Relaxed")
        col.prop(scene, "bio_walk_nervousness", slider=True, text="nervousness")
        col.label(text="Happy -- Sad")
        col.prop(scene, "bio_walk_happiness", slider=True, text="happiness")

        col.label(text="Actions")
        col.operator("scene.bio_walk_generate_walker", text="Generate")
        col.operator("scene.bio_walk_reset_walker", text="Reset")


def register():
    bpy.types.Scene.bio_walk_scale = bpy.props.FloatProperty(default=1, min=0)
    bpy.types.Scene.bio_walk_speed = bpy.props.FloatProperty(default=1, min=0)
    bpy.types.Scene.bio_start = bpy.props.IntProperty(default=1, min=0)
    bpy.types.Scene.bio_end = bpy.props.IntProperty(default=250, min=0)
    bpy.types.Scene.bio_key_frame_resolution = bpy.props.IntProperty(default=3, min=0)

    bpy.types.Scene.bio_walk_gender = bpy.props.FloatProperty(default=0, max=1, min=-1)
    bpy.types.Scene.bio_walk_weight = bpy.props.FloatProperty(default=0, max=1, min=-1)
    bpy.types.Scene.bio_walk_nervousness = bpy.props.FloatProperty(
        default=0, max=1, min=-1
    )
    bpy.types.Scene.bio_walk_happiness = bpy.props.FloatProperty(
        default=0, max=1, min=-1
    )

    bpy.utils.register_class(WalkerAddonPreferences)
    bpy.utils.register_class(ResetWalker)
    bpy.utils.register_class(GenerateWalker)
    bpy.utils.register_class(WalkCyclePanel)


def unregister():
    bpy.utils.unregister_class(WalkerAddonPreferences)
    bpy.utils.unregister_class(ResetWalker)
    bpy.utils.unregister_class(GenerateWalker)
    bpy.utils.unregister_class(WalkCyclePanel)


if __name__ == "__main__":
    register()
