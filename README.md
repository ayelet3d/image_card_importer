# image_card_importer
A tool for Autodesk Maya that lets the user select image files, and creates image cards with the same proportions.

installation:
1.Quit Maya if it is running 
2.put the "image_card_importer" folder inside maya's scripts folder: "C:\Users\<user_name>\Documents\maya\<maya_version>\scripts"
3.to add the tool shelf button- open the tab of the shelf that will contain the button, and drag and drop "drop_to_create_shelf_button.py" into the Maya viewport.
4.the button is now created, and will work when you restart maya.  

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
