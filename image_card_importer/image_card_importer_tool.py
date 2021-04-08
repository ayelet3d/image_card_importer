import pymel.core as pm
import ntpath
import os

"""
Image Card Importer Tool

the Image Card Importer tool lets the user select image files, and creates image cards with the same proportions. 

UI elements: 
image card prefix: allows the user to enter the prefix for the image cards and all related nodes that will be created.
alpha channel: when checked, the image transparency will be connected to the plane material and will show in viewport. 
               this option is recommended for png files with transparent background   
image sequence: when checked, will let the user select one image file and play the image sequence.
                please select a numbered file inside a folder that contains numbered image sequence files. 
scale ratio: when checked, lets you enter a number which will be the scale multiplier of the card dimensions. 
             the default is 2, so the width and length 1024 X 2048 will become 2048 X 4096. 
             the proportions will always stay the same.
import file button: when pressed, opens a dialog that allows the user to select the image files.   
           
"""


def get_files_input(single_file_selection):
    """
    opens a file dialog box with filter to show only image files, lets the user select a number of files

    :param single_file_selection: a flag, if true- selection will be only one file
    :return: an array of strings, list of image files paths selected by user
    """
    image_filter = "Image files (*.jpg *.jpeg *.jpe *.jfif *.png *.tif *.exr)"
    file_mode = 4
    if single_file_selection:
        file_mode = 1
    files_input = pm.fileDialog2(dialogStyle=2, fm=file_mode, ff=image_filter, cap="select images")
    return files_input


def process_name(path, pref, flag_seq):
    """
    extracts short name from path, cleans it and adds prefix to it

    :param path: a string, file path
    :param pref: a string, name prefix
    :param flag_seq: a flag, is the path of a sequence
    :return: a string, the processed name
    """
    # extract short name from path
    short_name = ntpath.basename(os.path.splitext(path)[0])
    # clean spaces and dots
    short_name = short_name.replace(" ", "_")
    if flag_seq:
        if "." in short_name and short_name[0] != ".":
            short_name = short_name.split(".")[0]
            short_name += "_sequence"
    for char in short_name:
        print(char)
        if not char.isalnum():
            print("yesy")
            short_name = short_name.replace(char, "_")
    # add prefix
    pref_name = pref + short_name

    return pref_name


def create_file_node(path, name):
    """
    creates a file node connected to a place2dTexture node, and sets the file path to given path

    :param path: a string, image file path
    :param name: a string, the name for the nodes creation. gets a suffix according to node type
    :return: a PyNode, the file node created
    """
    file_node = pm.shadingNode('file', n=name + "_file", asTexture=1, isColorManaged=1)
    p2d_node = pm.shadingNode('place2dTexture', name=name + "_place2dTexture", asUtility=1)
    attribute_list = ["coverage", "translateFrame", "rotateFrame", "mirrorU", "mirrorV",
                      "stagger", "wrapU", "wrapV", "repeatUV", "offset", "rotateUV", "noiseUV",
                      "vertexUvOne", "vertexUvTwo", "vertexUvThree", "vertexCameraOne"]
    for at in attribute_list:
        p2d_node.attr(at) >> file_node.attr(at)
    p2d_node.outUV >> file_node.uv
    p2d_node.outUvFilterSize >> file_node.uvFilterSize
    file_node.ftn.set(path)
    return file_node


def create_lambert_mtl(name):
    """
    creates a lambert shader with a shading grp

    :param name: a string, the name for the nodes creation
    :return: an array PyNodes; the shader, the shading grp
    """
    shd = pm.shadingNode('lambert', n=name + "_mtl", asShader=1)
    shdSG = pm.sets(n=shd.name() + 'SG' % shd, em=1, renderable=1, noSurfaceShader=1)
    shd.outColor >> shdSG.surfaceShader
    return shd, shdSG


def create_ratio_plane(file_node, name, flag_alpha, mult):
    """
    -gets a file node and creates a poly plane with the file node image proportions
    -calls the method create_lambert_mtl() to create a lambert shader and connects the file node to it
    -assigns the shader to the plane

    :param file_node: a PyNode, file node
    :param name: a string, the name for the nodes creation
    :param flag_alpha: a flag, indicates if to connect the transparency as well
    :param mult: a float, if not None - used as a uniform multiplier for the plane proportions in creation
    :return: a PyNode, poly plane
    """
    size_x = file_node.osx.get()
    size_y = file_node.osy.get()
    print(size_x, size_y)
    if not mult is None:
        size_x *= mult
        size_y *= mult

    poly_plane, ch = pm.polyPlane(sx=1, sy=1, w=size_x, h=size_y, n=name + "_card")
    ch.rename(name + "_polyPlane")

    # create shader 
    shd, shdSG = create_lambert_mtl(name)
    file_node.outColor >> shd.attr("color")

    # handle alpha 
    if flag_alpha:
        file_node.outTransparency >> shd.transparency

    # assign shader to plane
    pm.sets(shdSG, forceElement=poly_plane)
    return poly_plane


def add_item_to_grp(item, pref):
    """
    parents item into a grp, it grp in the requested name does not exist- creates one

    :param item: a PyNode, transform
    :param pref: a string, name prefix
    :return: a PyNode, transform- the grp created
    """
    grp_name = pref + "card_grp"
    if not pm.objExists(grp_name):
        grp = pm.group(em=1, n=grp_name)
    else:
        grp = pm.PyNode(grp_name)
    pm.parent(item, grp)
    pm.select(cl=1)
    return grp


def warn_if_name_exists(name):
    """
    checks if an object of the name exists in the scene

    :param name: a string, a name
    :return: a string or None, a warning if an object of the name exists in the scene, None if not
    """
    if pm.objExists(name):
        warning = "Warning: an object with the name " + name + " already exists. This may result in unpredicted naming"
    else:
        warning = None
    return warning


def handle_sequence(file_node):
    """
    receives a file node and enables use image sequence
    due to some viewport display issues- invokes attribute editor toggle and file selection

    :param file_node: a PyNode, file node
    """
    file_node.useFrameExtension.set(1)
    pm.runtime.ToggleAttributeEditor()
    pm.select(file_node)


def convert_to_float_if_number(string):
    """
    tries to convert string to float and returns it, if fails- returns None

    :param string: a string
    :return: a float or None
    """
    try:
        mult = float(string)
    except ValueError:
        mult = None
    return mult


def check_name_validity(string):
    """
    checks if a name can be used as a name for an object in maya

    :param string: a string, a name
    :return: an array, list of errors
    """
    error_list = []
    # remove underscores
    string = string.replace("_", "")
    if string[0].isdigit():
        error = "Error: a name cannot start with a number"
        error_list.append(error)
    if not string.isalnum():
        error = "Error: a name cannot contain symbols other then letters, numbers and underscores"
        error_list.append(error)
    return error_list


def main_import_images(img_pref_input, flag_alpha, flag_scale, size_mult_input, flag_seq):
    """
    image card importer main function

    - handling errors: checking img_pref_input and size_mult_input
    - invokes user image file selection, if the user selects them continues
    - if the flag_scale is on, processes the size multiplier input
    - process the image card name for all the nodes that will be created
     -warns if the names of the nodes about to be created already exists
    - creates the image card and adds it to a grp
    - if the flag_seq is on, handles sequence
    - prints warnings
    :param img_pref_input: a string, name prefix
    :param flag_alpha: a flag, whether or not to use alpha
    :param flag_scale: a flag, , whether or not to use scale multiplier
    :param size_mult_input: a string, multiplier number
    :param flag_seq: a flag, whether or not the card image will be a sequence
    :return:
    """

    error_list = []
    warning_list = []

    name_errors = check_name_validity(img_pref_input)
    error_list += name_errors

    mult = None
    if flag_scale:
        mult = convert_to_float_if_number(size_mult_input)
        if mult is None:
            error = "Error: the input \"" + size_mult_input + "\" for Scale Ratio is not a number. please type a number"
            error_list.append(error)

    if error_list:
        errors_string = ""
        for error in error_list:
            errors_string += error + "\n"

        pm.confirmDialog(title='Error', message=errors_string, button='OK', defaultButton='OK', cancelButton='OK')
    else:
        imgs_files = get_files_input(flag_seq)
        if imgs_files is not None:
            for path in imgs_files:
                main_name = process_name(path, img_pref_input, flag_seq)
                name_suffixes = ["_file", "_place2dTexture", "_mtl", "_card"]
                for suff in name_suffixes:
                    warning = warn_if_name_exists(main_name + suff)
                    if warning is not None:
                        warning_list.append(warning)
                file_node = create_file_node(path, main_name)
                poly_plane = create_ratio_plane(file_node, main_name, flag_alpha, mult)
                add_item_to_grp(poly_plane, img_pref_input)
                if flag_seq:
                    handle_sequence(file_node)
        for warning in warning_list:
            print(warning)


class window_ui(object):
    WINDOW_NAME = "images_importer"

    cb_alpha = None
    cb_scale = None
    cb_seq = None
    size_mult_input = None
    img_pref_input = None

    @classmethod
    def display(cls):
        """
        creates and displays a window

        """
        # window UI
        window_name = cls.WINDOW_NAME
        title = "Images Importer"

        if pm.window(window_name, ex=True):
            pm.deleteUI(window_name)
            pm.windowPref(window_name, remove=1)

        main_window = pm.window(window_name, t=title, iconName='icon_Name', wh=(280, 190), s=1, tb=1)

        form = pm.formLayout(numberOfDivisions=100)

        sep0 = pm.separator(style="in", h=3)
        rows = pm.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 110), (2, 130)])
        pm.text(label='Image Card Prefix: ', al="right")
        cls.img_pref_input = pm.textField(tx="img_")
        pm.setParent('..')

        sep1 = pm.separator(style="in", h=3)
        cls.cb_alpha = pm.checkBox(l="Alpah Channel", al="center")
        cls.cb_scale = pm.checkBox(l="Scale Ratio", al="center",
                                   changeCommand="from image_card_importer.image_card_importer_tool import window_ui\n"
                                                 "window_ui.cb_scale_toggled()")
        cls.size_mult_input = pm.textField(tx="2", enable=0)
        cls.cb_seq = pm.checkBox(l="Image Sequence", al="center")

        sep2 = pm.separator(style="in", h=3)
        btn_notes_txt = pm.text(label='Please select image files to import as cards', al="center",
                                font="obliqueLabelFont")
        btn_import = pm.button(l="Import Images", al="center", h=30, w=150)
        btn_import.setCommand(
            "from image_card_importer.image_card_importer_tool import window_ui\nwindow_ui.import_button()")

        pm.formLayout(form, edit=True,
                      attachForm=[
                          (sep0, 'left', 5), (sep0, 'right', 5),
                          (sep0, 'top', 0),
                          (rows, 'left', 10), (rows, 'right', 10),
                          (cls.cb_alpha, 'left', 20),
                          (btn_notes_txt, 'left', 40),
                          (cls.cb_scale, 'left', 20),
                          (sep1, 'left', 5), (sep1, 'right', 5),
                          (sep2, 'left', 5), (sep2, 'right', 5),
                          (btn_import, 'left', 65),
                      ],

                      attachControl=[
                          (rows, 'top', 10, sep0),
                          (cls.cb_alpha, 'top', 10, sep1),
                          (cls.cb_seq, 'top', 10, sep1),
                          (cls.cb_seq, 'left', 12, cls.cb_alpha),
                          (cls.cb_scale, 'top', 10, cls.cb_seq),
                          (cls.size_mult_input, 'top', 10, cls.cb_seq),
                          (cls.size_mult_input, 'left', 30, cls.cb_scale),
                          (sep1, 'top', 10, rows),
                          (sep2, 'top', 10, cls.cb_scale),
                          (btn_notes_txt, 'top', 10, sep2),
                          (btn_import, 'top', 10, btn_notes_txt),

                      ]

                      )

        pm.showWindow(main_window)

        pm.columnLayout()

    @classmethod
    def cb_scale_toggled(cls):
        """
        enables the textfield if the checkbox is checked, disables if unchecked
        :return:
        """
        cb_enabled = pm.checkBox(cls.cb_scale, query=1, value=1)
        pm.textField(cls.size_mult_input, edit=True, enable=cb_enabled)

    @classmethod
    def import_button(cls, *args):
        """
        collects UI user input and calls main_import_images to start the tool process
        :param args:
        :return:
        """
        # get UI data
        img_pref = pm.textField(cls.img_pref_input, q=1, text=1)
        flag_alpha = pm.checkBox(cls.cb_alpha, q=1, value=1)
        flag_scale = pm.checkBox(cls.cb_scale, q=1, value=1)
        size_mult_input = pm.textField(cls.size_mult_input, q=1, text=1)
        flag_seq = pm.checkBox(cls.cb_seq, q=1, value=1)
        main_import_images(img_pref, flag_alpha, flag_scale, size_mult_input, flag_seq)
