import json
import os
import bpy
import traceback
from . import algorithms

def populate_modifier(mod, m):
    mod.active = m['active']
    mod.blend_in = m['blend_in']
    mod.blend_out = m['blend_out']
    mod.influence = m['influence']
    mod.mode = m['mode']
    mod.mute = m['mute']
    mod.poly_order = m['poly_order']
    # type should be created when the modifier is created
    #mod.type = m['type']
    mod.use_additive = m['use_additive']
    mod.use_influence = m['use_influence']
    mod.coefficients[0] = m['coefficients'][0]
    mod.coefficients[1] = m['coefficients'][1]

def populate_modifiers(modifiers, mlist):
    i = 0
    mod = modifiers[0]
    for m in mlist:
        if i == 0:
            populate_modifier(mod, m)
            i = i + 1
        else:
            mod = modifiers.new(m['type'])
            populate_modifier(mod, m)

def create_variable(var, driver):
    face_rig = bpy.data.objects[var['targets'][0]['id_name']]

    v = driver.driver.variables.new()

    v.name = var['name']
    v.type = var['type']
    # we have one target by default
    v.targets[0].id = face_rig
    v.targets[0].transform_space = var['targets'][0]['transform_space']
    v.targets[0].transform_type = var['targets'][0]['transform_type']
    v.targets[0].bone_target = var['targets'][0]['bone_target']

def rm_drivers():
    mesh = algorithms.get_active_body()
    mname = mesh.name

    for d in bpy.data.objects[mname].data.shape_keys.key_blocks:
        rc = d.driver_remove('value')
        if not rc:
            algorithms.print_log_report("CRITICAL", "failed to removed a driver:".format(rc))

def add_drivers(drivers):
    # Iterate through each driver entry and create driver
    mesh = algorithms.get_active_body()
    mname = mesh.name
    for k, v in drivers.items():
        shape_name = v['data_path'].strip('key_blocks["').strip('"].value')
        idx = bpy.data.objects[mname].data.shape_keys.key_blocks.find(shape_name)
        if idx == -1:
            algorithms.print_log_report("CRITICAL", "{0} shape key not found".format(shape_name))
            continue
        check = bpy.data.objects[mname].data.shape_keys.animation_data and \
                bpy.data.objects[mname].data.shape_keys.animation_data.drivers.\
                    find(v['data_path'])
        if check:
            algorithms.print_log_report("CRITICAL", "{0} shape key already has animation data".format(shape_name))
            continue

        # NOTE: The call to driver_add adds a modifier of type GENERATOR
        # automatically
        driver = bpy.data.objects[mname].data.shape_keys.key_blocks[idx]. \
                    driver_add('value')

        # Populate the driver
        driver.hide = v['hide']
        driver.lock = v['lock']
        driver.mute = v['mute']
        driver.select = v['select']
        populate_modifiers(driver.modifiers, v['modifiers'])
        driver.driver.expression = v['driver']['expression']
        driver.driver.is_valid = v['driver']['is_valid']
        driver.driver.type = v['driver']['type']
        driver.driver.use_self = v['driver']['use_self']
        variables = v['driver']['variables']
        for var in variables:
            create_variable(var, driver)

def add_facs_drivers(skd):
    au_div = skd['Divisor']['au_value']
    gz_div = skd['Divisor']['gz_value']

    mesh = algorithms.get_active_body()
    mname = mesh.name

    for au, exprs in skd.items():
        if au == 'Divisor':
            continue

        # get the object
        slider = "facs_rig_slider_"+au
        slider_obj = bpy.data.objects.get(slider)
        if not slider_obj:
            algorithms.print_log_report("CRITICAL", "{0} slider controller not found".format(slider))
            continue

        # iterate over all the expressions which are part of this AU
        for skn, skv in exprs.items():
            # Look up the shape key
            idx = bpy.data.objects[mname].data.shape_keys.key_blocks.find(skn)
            if idx == -1:
                algorithms.print_log_report("CRITICAL", "{0} shape key not found".format(skn))
                continue

            # Add a variable for the AU
            data_path = 'key_blocks["'+skn+'"].value'
            no_animation = not bpy.data.objects[mname].data.shape_keys.animation_data

            if no_animation:
                algorithms.print_log_report("CRITICAL", "FACS system depends on facial rig. Please add one")
                return -1

            # get the driver
            driver = bpy.data.objects[mname].data.shape_keys.animation_data.drivers.find(data_path)
            if not driver:
                algorithms.print_log_report("CRITICAL", "FACS system depends on facial rig. Please add one")
                return -1

            # Add the variable for the Action Unit
            v = driver.driver.variables.new()

            v.name = au
            v.type = 'TRANSFORMS'
            # we have one target by default
            v.targets[0].id = slider_obj
            v.targets[0].transform_space = 'LOCAL_SPACE'
            v.targets[0].transform_type = 'LOC_X'

            # append to the existing expression
            # max_slider_value * constant = max_shape_key_value
            # constant = max_shape_key_value / max_slider_value
            # Formula for transforming slider value to shape key value is
            #       shape_key_value = slider_value * constant
            # slider value is extracted from the variable we created
            if au == 'GZ0H' or au == 'GZ0V':
                constant = skv / gz_div
                if '_min' in skn:
                    driver.driver.expression = driver.driver.expression + '+ ('+au+'*'+str(constant)+')'
                elif '_max' in skn:
                    driver.driver.expression = driver.driver.expression + '+ (-'+au+'*'+str(constant)+')'
            else:
                constant = skv / au_div
                driver.driver.expression = driver.driver.expression + '+ ('+au+'*'+str(constant)+')'

    return 0

def append_rig(rig_name, data_path):
    face_rig_blend = os.path.join(data_path, "face_rig", "face_rig_lib.blend")

    if not os.path.exists(face_rig_blend):
        algorithms.print_log_report("CRITICAL", "{0} not found. Might need to reinstall ManuelBastioniLab".format(face_rig_blend))
        return False

    file_path = face_rig_blend+"\\"+"Collection\\"+rig_name
    directory = face_rig_blend+"\\"+"Collection"
    try:
        bpy.ops.wm.append(filepath=file_path, filename=rig_name, directory=directory)
    except RuntimeError as e:
        algorithms.print_log_report("CRITICAL", "{0}".format(str(e)))
        return False

    return True


def setup_face_rig():
    # check if the face rig is already imported
    if bpy.data.objects.find('MBLab_skeleton_face_rig') != -1:
        algorithms.print_log_report("CRITICAL", "MBLab_skeleton_face_rig is already imported")
        return False

    data_path = algorithms.get_data_path()

    # Load the face rig
    if not data_path:
        algorithms.print_log_report("CRITICAL", "{0} not found. Please check your Blender addons directory. Might need to reinstall ManuelBastioniLab".format(data_path))
        return False

    if not append_rig('Face_Rig', data_path) or \
       not append_rig('Phoneme_Rig', data_path):
        return False

    # load face rig json file
    json_file = os.path.join(data_path, "face_rig", "expression_drivers.json")

    if not os.path.exists(json_file):
        algorithms.print_log_report("CRITICAL", "{0} not found. Might need to reinstall ManuelBastioniLab".format(json_file))
        return False

    with open(json_file, 'r') as f:
        drivers = json.load(f)
        add_drivers(drivers)

    return True

def setup_facs_rig():
    # check if the facs rig is already imported
    if bpy.data.objects.find('MBLab_facs_rig') != -1:
        algorithms.print_log_report("CRITICAL", "MBLab_facs_rig is already imported")
        return False

    data_path = algorithms.get_data_path()

    # Load the face rig
    if not data_path:
        algorithms.print_log_report("CRITICAL", "{0} not found. Please check your Blender addons directory. Might need to reinstall ManuelBastioniLab".format(data_path))
        return False

    if not append_rig('Facs_Rig', data_path):
        return False

    # load face rig json file
    json_file = os.path.join(data_path, "face_rig", "facs_au.json")

    if not os.path.exists(json_file):
        algorithms.print_log_report("CRITICAL", "{0} not found. Might need to reinstall ManuelBastioniLab".format(json_file))
        return False

    with open(json_file, 'r') as f:
        shape_keys = json.load(f)
        try:
            add_facs_drivers(shape_keys)
        except Exception as e:
            traceback.print_stack()
            algorithms.print_log_report("CRITICAL", "{0}".format(str(e)))
            return False

    return True

def recursive_collection_delete(head):
    for c in head.children:
        recursive_collection_delete(c)

    head.hide_select = False
    head.hide_render = False
    head.hide_viewport = False

    for obj in head.all_objects:
        obj.select_set(True)
    bpy.ops.object.delete()

    bpy.data.collections.remove(head)

def delete_face_rig():
    # check if the face rig is already imported
    facerig = bpy.data.objects.get('MBLab_skeleton_face_rig')
    if not facerig:
        algorithms.print_log_report("CRITICAL", "face rig is not added")
        return False

    # check if the face rig is already imported
    phoneme = bpy.data.objects.get('MBLab_skeleton_phoneme_rig')
    if not phoneme:
        algorithms.print_log_report("CRITICAL", "phoneme rig is not added")
        return False

    rm_drivers()

    # store the original selection
    orig_selection = {}
    for ob in bpy.context.scene.objects:
        orig_selection[ob.name] = ob.select_get()
        ob.select_set(False)

    # delete all the rigs
    facerig.select_set(True)
    phoneme.select_set(True)
    bpy.ops.object.delete()

    # delete all the collections
    c = bpy.data.collections.get('Face_Rig')
    if c:
       recursive_collection_delete(c)
    c = bpy.data.collections.get('Facs_Rig')
    if c:
       recursive_collection_delete(c)
    c = bpy.data.collections.get('Phoneme_Rig')
    if c:
       recursive_collection_delete(c)

    # restore the original selection
    for ob in bpy.context.scene.objects:
        ob.select_set(orig_selection[ob.name])

    return True

