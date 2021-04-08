import os
import pymel.core as pm
import maya.mel as mel


def onMayaDroppedPythonFile(obj):
    """
    the onMayaDroppedPythonFile method
    this method name is recognized by maya and is being called when the file is dropped inside the viewport.

    creates a shelf button for the Image Card Importer tool.
    raises an error if the Image Card Importer folder is not located inside the scripts folder.

    """

    # get the dropped file location
    path = os.path.dirname(os.path.abspath(__file__))
    parent_path = os.path.abspath(os.path.join(path, os.pardir))

    # get maya scripts folder path
    scripts_path = pm.internalVar(usd=True)
    scripts_path = scripts_path.replace("/", "\\")

    if scripts_path[-1] == "\\":
        scripts_path = scripts_path[:-1]

    # compare the paths and if the current file path is not maya scripts folder, raise an error.
    if parent_path != scripts_path:
        error_string = "the image_card_importer folder is inside in the incorrect folder.\nthe correct folder is: " + scripts_path
        pm.confirmDialog(title='Error', message=error_string, button='OK', defaultButton='OK', cancelButton='OK')

    else:

        icon_directory = os.path.join(path, "icons")
        image_path = os.path.join(icon_directory, "image_card_importer_icon.png")

        # get current top shelf
        top_shelf = mel.eval('$nul = $gShelfTopLevel')

        # create a shelf button on current top shelf
        if pm.windows.tabLayout(top_shelf, e=1):
            pm.windows.shelfButton(parent=top_shelf + "|" + pm.windows.tabLayout(top_shelf, q=1, st=1),
                                   annotation='Image Card Importer',
                                   image1=image_path,
                                   command="import image_card_importer.image_card_importer_tool as im\n"
                                           "win = im.window_ui()\n"
                                           "win.display()",
                                   )
