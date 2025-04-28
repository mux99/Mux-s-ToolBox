"""
script to change the priority value of EDI 'ISO 20022'
"""
import os
import shutil

editPath = "Z:/Finances/Compta/SEPA_EURELEC_EDI/Nouveaux"
ccPath = "Z:/Finances/Compta/SEPA_EURELEC_EDI/Originaux"
archiveOld = True
xmlMarker = "InstrPrty"
newPriority = "HIGH"

def moveToSub(path, extention=".xml", subDir="old"):
    """ Move files to old subfolder
    path:       path of the directory in which to perform the action
    extention:  specify the extention, if empty string everything is moved
    subDir:     specify the subdirectory of path to move the files to
    """
    for path in os.listdir(ccPath):
        if path == subDir:
            continue
        if len(extention) == 0 or path[-len(extention):] == extention:
            shutil.move(f"{ccPath}/{path}", f"{ccPath}/{subDir}/")

def replaceText(path, target, new):
    """ Replace target text in a file
    path:   path to the file to be edited
    target: target text to replace
    new:    new text
    """
    with open(path, "r") as file:
        filedata = file.read()
    filedata = filedata.replace(target, new)
    with open(path, "w") as file:
        file.write(filedata)


if __name__ == "__main__":
    
    #move already present files to 'old/'
    if archiveOld:
        moveToSub(ccPath)

    #operations on new files
    files = os.listdir(editPath)
    for path in files:
        if path[-4:] != '.xml':
            continue
        
        #copy file to cc path
        shutil.copy2(f"{editPath}/{path}", f"{ccPath}")

        #edit with new status
        replaceText(f"{editPath}/{path}", f"<{xmlMarker}>NORM</{xmlMarker}>", f"<{xmlMarker}>{newPriority}</{xmlMarker}>")

    