import bpy
import os
import json
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.app.handlers import persistent
from . import humanoid, animationengine, proxyengine
from . import facerig
from . import algorithms
import time
import ctypes
import sys
import platform
from bpy.props import EnumProperty, StringProperty, BoolVectorProperty

addon_path = os.path.dirname(os.path.realpath(__file__))
yasp_sphinx_dir = os.path.join(addon_path, "yasp", "sphinxinstall", "lib")
yasp_libs_dir = os.path.join(addon_path, "yasp", "yaspbin")
sys.path.append(yasp_libs_dir)
pocketsphinxlib = None
sphinxadlib = None
sphinxbaselib = None
yasplib = None

# Load the .so files we need
# Then import yasp
# Now we're ready to do some speech parsing
def yasp_load_dep():
    pocketsphinx = os.path.join(yasp_sphinx_dir, "libpocketsphinx.so")
    sphinxad = os.path.join(yasp_sphinx_dir, "libsphinxad.so")
    sphinxbase = os.path.join(yasp_sphinx_dir, "libsphinxbase.so")
    yasp = os.path.join(yasp_libs_dir, "_yasp.so")
    try:
        pocketsphinxlib = ctypes.cdll.LoadLibrary(pocketsphinx)
        sphinxadlib = ctypes.cdll.LoadLibrary(sphinxad)
        sphinxbaselib = ctypes.cdll.LoadLibrary(sphinxbase)
        yasplib = ctypes.cdll.LoadLibrary(yasp)
    except:
       print("Failed to load libraries")

yasp_load_dep()
import yasp

# class maps yasp phoneme Mapper
# YASP produces a more nuanced phonemes. We need to reduce that to the set
# of phonemes which we use for the animation
class YASP2MBPhonemeMapper(object):
    def __init__(self):
        self.yasp_2_mb_phoneme_map = None
        data_path = algorithms.get_data_path()
        if not data_path:
            algorithms.print_log_report("CRITICAL", "{0} not found. Please check your Blender addons directory. Might need to reinstall ManuelBastioniLab".format(data_path))
            raise ValueError("No Data directory")

        map_file = os.path.join(data_path, 'face_rig', 'yasp_map.json')
        if not map_file:
            algorithms.print_log_report("CRITICAL", "{0} not found. Please check your Blender addons directory. Might need to reinstall ManuelBastioniLab".format(map_file))
        with open(map_file, 'r') as f:
            self.yasp_2_mb_phoneme_map = json.load(f)

    def get_phoneme_animation_data(self, phoneme):
        try:
            anim_data = self.yasp_2_mb_phoneme_map[phoneme]
        except:
            return None
        return anim_data

# each sequence can have multiple markers associated with it.
class Sequence(object):
    def __init__(self, seq):
        self.sequence = seq
        self.markers = []

    # Markers are added in sequential order
    def add_marker(self, m):
        self.markers.append(m)

    def del_marker(self, m):
        if m in self.markers:
                self.markers.remove(m)

    def rm_marker_from_scene(self, scn):
        for m in self.markers:
            scn.timeline_markers.remove(m)
        self.markers = []

    def is_sequence(self, s):
        return (self.sequence == s)

    def mark_seq_at_frame(self, mname, frame, scn):
        m = scn.timeline_markers.new(mname, frame=frame)
        self.markers.append(m)

    def move_to_next_marker(self, scn):
        cur_frame = scn.frame_current
        found = False
        for m in self.markers:
            if m.frame > cur_frame:
                found = True
                break
        if found:
            scn.frame_current = m.frame

    def move_to_prev_marker(self, scn):
        cur_frame = scn.frame_current
        found = False
        for m in reversed(self.markers):
            if m.frame < cur_frame:
                found = True
                break
        if found:
            scn.frame_current = m.frame

    def reset_all_bones(self, bones, frame):
        for bone in bones:
            bone.rotation_quaternion[3] = 0
            bone.keyframe_insert('rotation_quaternion', index=3, frame=frame)

    # go through the markers on the selected sequence.
    # for each marker look up the marker name in our mapper
    # Set the corresponding bones in the list to the values specified.
    def animate_all_markers(self):
        idx = 0
        bpy.ops.pose.select_all(action='DESELECT')
        for m in self.markers:
            self.set_keyframe(m, idx)
            idx = idx + 1

    def animate_marker_at_frame(self, cur_frame):
        idx = 0
        found = False
        for m in self.markers:
            if m.frame == cur_frame:
                found = True
                break
            idx = idx + 1

        if found:
            print(m.frame, idx)
            self.set_keyframe(m, idx)

    def del_all_keyframes(self):
        idx = 0
        for m in self.markers:
            if idx == 0:
                frame = (m.frame - 1) / 2
                self.del_keyframe(frame)
                idx = idx + 1
            self.del_keyframe(m.frame)

    def del_keyframe(self, frame):
        for bone in bpy.context.object.pose.bones:
            bone.keyframe_delete('rotation_quaternion', index=3, frame=frame)

    def set_keyframe(self, m, idx):
        if idx == 0:
            frame = (m.frame - 1) / 2
            self.reset_all_bones(bpy.context.object.pose.bones, frame)
        self.reset_all_bones(bpy.context.object.pose.bones, m.frame)

        phonemes = yaspmapper.get_phoneme_animation_data(m.name)
        if not phonemes:
            print("Can't find corresponding mapping for:", m.name)
            return
        prev_phonemes = phonemes
        for phone in phonemes:
            bone_name = 'ph_'+phone[0]
            bone = bpy.context.object.pose.bones[bone_name]
            bone.rotation_quaternion[3] = phone[1]
            print(bone_name,':', m.frame, ':', phone[1])
            bone.keyframe_insert('rotation_quaternion', index=3, frame=m.frame)

class SequenceMgr(object):
    def __init__(self):
        self.sequences = []
        self.orig_frame_set = False

    def set_orig_frame(self, scn):
        if not self.orig_frame_set:
            self.orig_frame_start = scn.frame_start
            self.orig_frame_end = scn.frame_end
            self.orig_frame_set = True

    def add_sequence(self, s):
        seq = Sequence(s)
        self.sequences.append(seq)

    def del_sequence(self, s):
        if s in self.sequences:
                self.sequences.remove(s)

    def get_sequence(self, s):
        for seq in self.sequences:
            if seq.is_sequence(s):
                return seq
        return None

    def unmark_sequence(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.rm_marker_from_scene(scn)

    def rm_seq_from_scene(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        scn.sequence_editor.sequences.remove(s)
        seq.rm_marker_from_scene(scn)
        self.del_sequence(seq)

    def mark_seq_at_frame(self, s, mname, frame, scn):
        seq = self.get_sequence(s)
        if not seq:
            return False
        seq.mark_seq_at_frame(mname, frame, scn)

    def move_to_next_marker(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.move_to_next_marker(scn)

    def move_to_prev_marker(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.move_to_prev_marker(scn)

    def animate_all_markers(self, s):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.animate_all_markers()

    def animate_current(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.animate_marker_at_frame(scn.frame_current)

    def del_keyframe(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.del_keyframe(scn.frame_current)

    def del_all_keyframes(self, s, scn):
        seq = self.get_sequence(s)
        if not seq:
            return
        seq.del_all_keyframes()

    def restore_start_end_frames(self):
        bpy.context.scene.frame_start = self.orig_frame_start
        bpy.context.scene.frame_end = self.orig_frame_end

seqmgr = SequenceMgr()
yaspmapper = YASP2MBPhonemeMapper()

class YASP_OT_mark(bpy.types.Operator):
    bl_idname = "yasp.mark_audio"
    bl_label = "Mark"
    bl_description = "Run YASP and mark audio"

    def mark_audio(self, json_str, offset, seq, scn):
        jdict = json.loads(json_str)
        word_list = []
        # iterate over the json dictionary to and create markers
        try:
            word_list = jdict['words']
        except:
            return False

        for word in word_list:
            try:
                phonemes = word['phonemes']
            except:
                return False
            for phone in phonemes:
                try:
                    # calculate the frame to insert the marker
                    frame = round((scn.render.fps/scn.render.fps_base) *
                                  (phone['start'] / 100))
                    cur_frame = offset + frame
                    #print(cur_frame, frame)
                    seqmgr.mark_seq_at_frame(seq, phone['phoneme'], cur_frame, scn)
                except Exception as e:
                    print(e)
                    print('something else is wrong')
                    return False
        return True

    def free_json_str(self, json_str):
        yasp.yasp_free_json_str(json_str)

    def run_yasp(self, wave, transcript, offset):
        if not wave or not transcript:
            self.report({'ERROR'}, "bad wave or transcript files")
            return None

        logs = yasp.yasp_logs()
        yasp.yasp_setup_logging(logs, None, "MB_YASP_Logs")
        json_str = yasp.yasp_interpret_get_str(wave, transcript, None)
        yasp.yasp_finish_logging(logs)
        if not json_str:
            self.report({'ERROR'}, "Couldn't parse speech")
            return None
        if os.path.exists("MB_YASP_Logs"):
            os.remove("MB_YASP_Logs")

        return json_str

    def execute(self, context):
        scn = context.scene
        wave = scn.yasp_wave_path
        transcript = scn.yasp_transcript_path

        if not os.path.isfile(wave) or \
           not os.path.isfile(transcript):
            self.report({'ERROR'}, 'Bad path to wave or transcript')
            return {'FINISHED'}

        if not scn.yasp_start_frame:
            start_frame = 1
        else:
            try:
                start_frame = int(scn.yasp_start_frame)
            except:
                self.report({'ERROR'}, 'Bad start frame')
                return {'FINISHED'}

        json_str = self.run_yasp(wave, transcript, start_frame)
        if not json_str:
            return {'FINISHED'}

        # find a free channel in the sequence editor
        channels = []
        for s in scn.sequence_editor.sequences_all:
            channels.append(s.channel)
        channels.sort()

        channel_select = 1
        for c in channels:
            if c > channel_select:
                break
            channel_select = c + 1
        #insert the wave file
        seq = scn.sequence_editor.sequences.new_sound(os.path.basename(wave), wave,
                   channel_select, start_frame)

        seqmgr.add_sequence(seq)

        if not self.mark_audio(json_str, start_frame, seq, scn):
            seqmgr.rm_seq_from_scene(seq, scn)
            self.report({'ERROR'}, 'Failed to mark the audio file')
            # some memory management
            self.free_json_str(json_str)
            return {'FINISHED'}

        # some memory management
        self.free_json_str(json_str)

        # set the end frame
        end = 0
        for s in scn.sequence_editor.sequences_all:
            if s.frame_final_end > end:
                end = s.frame_final_end
        scn.frame_end = end
        return {'FINISHED'}

class YASP_OT_unmark(bpy.types.Operator):
    bl_idname = "yasp.unmark_audio"
    bl_label = "Unmark"
    bl_description = "Unmark the audio file and remove"

    def execute(self, context):
        scn = context.scene

        seq = scn.sequence_editor.active_strip
        if seq and seq.select:
            seqmgr.unmark_sequence(seq, scn)
        else:
            self.report({'ERROR'}, 'Must select a strip to unmark')

        seqmgr.restore_start_end_frames()

        return {'FINISHED'}

class YASP_OT_delete_seq(bpy.types.Operator):
    bl_idname = "yasp.delete_seq"
    bl_label = "Remove Strip"
    bl_description = "Delete active sequence"

    def execute(self, context):
        scn = context.scene
        seq = scn.sequence_editor.active_strip
        if seq and seq.select:
            seqmgr.rm_seq_from_scene(seq, scn)
            if len(scn.sequence_editor.sequences_all) == 0:
                seqmgr.restore_start_end_frames()
        else:
            self.report({'ERROR'}, 'Must select a strip to delete')

        return {'FINISHED'}

def set_animation_prereq(scn):
    seq = scn.sequence_editor.active_strip
    if not seq or not seq.select:
        return 'STRIP_ERROR', None

    phoneme_rig = bpy.data.objects.get('MBLab_skeleton_phoneme_rig')
    if not phoneme_rig:
        return 'RIG_ERROR', None

    # select the rig and put it in POSE mode
    for obj in bpy.data.objects:
        obj.select_set(False)
    phoneme_rig.select_set(True)
    bpy.context.view_layer.objects.active = phoneme_rig
    bpy.ops.object.mode_set(mode='POSE')
    return 'SUCCESS', seq


class YASP_OT_setallKeyframes(bpy.types.Operator):
    bl_idname = "yasp.set_all_keyframes"
    bl_label = "Set All"
    bl_description = "Set all marked lip-sync keyframe"

    def execute(self, context):
        scn = context.scene
        rc, seq = set_animation_prereq(scn)
        if (rc == 'STRIP_ERROR'):
            self.report({'ERROR'}, "Must select a strip to operate on")
            return {'FINISHED'}
        elif (rc == 'RIG_ERROR'):
            self.report({'ERROR'}, "Phoneme Rig not found")
            return {'FINISHED'}

        # insert key frames on all markers.
        seqmgr.animate_all_markers(seq)
        return {'FINISHED'}

class YASP_OT_deleteallKeyframes(bpy.types.Operator):
    bl_idname = "yasp.delete_all_keyframes"
    bl_label = "Unset All"
    bl_description = "Set all marked lip-sync keyframe"

    def execute(self, context):
        scn = context.scene
        rc, seq = set_animation_prereq(scn)
        if (rc == 'STRIP_ERROR'):
            self.report({'ERROR'}, "Must select a strip to operate on")
            return {'FINISHED'}
        elif (rc == 'RIG_ERROR'):
            self.report({'ERROR'}, "Phoneme Rig not found")
            return {'FINISHED'}

        seqmgr.del_all_keyframes(seq, scn)
        return {'FINISHED'}

class YASP_OT_set(bpy.types.Operator):
    bl_idname = "yasp.set_keyframe"
    bl_label = "Set"
    bl_description = "Set a lip-sync keyframe"

    def execute(self, context):
        scn = context.scene
        rc, seq = set_animation_prereq(scn)
        if (rc == 'STRIP_ERROR'):
            self.report({'ERROR'}, "Must select a strip to operate on")
            return {'FINISHED'}
        elif (rc == 'RIG_ERROR'):
            self.report({'ERROR'}, "Phoneme Rig not found")
            return {'FINISHED'}

        seqmgr.animate_current(seq, scn)
        return {'FINISHED'}

class YASP_OT_unset(bpy.types.Operator):
    bl_idname = "yasp.del_keyframe"
    bl_label = "Unset"
    bl_description = "Unset a lip-sync keyframe"

    def execute(self, context):
        scn = context.scene
        rc, seq = set_animation_prereq(scn)
        if (rc == 'STRIP_ERROR'):
            self.report({'ERROR'}, "Must select a strip to operate on")
            return {'FINISHED'}
        elif (rc == 'RIG_ERROR'):
            self.report({'ERROR'}, "Phoneme Rig not found")
            return {'FINISHED'}

        seqmgr.animate_keyframe(seq, scn)
        return {'FINISHED'}

class YASP_OT_next(bpy.types.Operator):
    bl_idname = "yasp.next_marker"
    bl_label = "next"
    bl_description = "Jump to next marker"

    def execute(self, context):
        scn = context.scene

        seq = scn.sequence_editor.active_strip
        if seq and seq.select:
            seqmgr.move_to_next_marker(seq, scn)
        else:
            self.report({'ERROR'}, "Must select a strip")

        return {'FINISHED'}

class YASP_OT_prev(bpy.types.Operator):
    bl_idname = "yasp.prev_marker"
    bl_label = "prev"
    bl_description = "Jump to previous marker"

    def execute(self, context):
        scn = context.scene

        seq = scn.sequence_editor.active_strip
        if seq and seq.select:
            seqmgr.move_to_prev_marker(seq, scn)
        else:
            self.report({'ERROR'}, "Must select a strip")

        return {'FINISHED'}

class VIEW3D_PT_tools_mb_yasp(bpy.types.Panel):
    bl_label = "Speech Parser"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ManuelBastioniLAB"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scn = context.scene
        layout = self.layout
        wm = context.window_manager
        col = layout.column(align=True)

        seqmgr.set_orig_frame(scn)

        if platform.system() != "Linux":
            col.label(text="Linux only feature", icon='ERROR')
            return

        col.label(text="Path to WAV file")
        col.prop(scn, "yasp_wave_path", text='')
        col.label(text="Path to transcript file")
        col.prop(scn, "yasp_transcript_path", text="")
        col.label(text="Start on frame")
        col.prop(scn, "yasp_start_frame", text="")
        col = layout.column(align=True)
        row = col.row(align=False)
        row.operator('yasp.mark_audio', icon='MARKER_HLT')
        row.operator('yasp.unmark_audio', icon='MARKER')
        col = layout.column(align=True)
        col.operator('yasp.set_all_keyframes', icon='DECORATE_KEYFRAME')
        col = layout.column(align=True)
        col.operator('yasp.delete_all_keyframes', icon='KEYFRAME')
        col = layout.column(align=True)
        row = col.row(align=False)
        row.operator('yasp.set_keyframe', icon='KEYFRAME_HLT')
        row.operator('yasp.del_keyframe', icon='KEYFRAME')
        col = layout.column(align=True)
        row = col.row(align=False)
        row.operator('yasp.prev_marker', icon='PREV_KEYFRAME')
        row.operator('yasp.next_marker', icon='NEXT_KEYFRAME')
        col = layout.column(align=True)
        col.operator('yasp.delete_seq', icon='DECORATE_KEYFRAME')

