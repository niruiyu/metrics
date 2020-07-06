import os
import os.path
import glob
import sys
import argparse
import xml.etree.ElementTree as ET

def ConvertPath (workspace, remote, path):
  Path = []
  RemotePath = {
    None : "",
    "IntelRepo": "Intel\\",
    "IntelRemote" : "Intel\\",
    "EdkRepo" : "Edk2\\",
    "EdkRemote" : "Edk2\\",
    "Edk2PlatformsRemote" : "Edk2Platforms\\",
    "Edk2PlatformsRepo" : "Edk2Platforms\\",
    "SvRestrictedRepo" : "SvRestricted\\",
    "FDBinRemote" : "FDBin\\"
    }
  for p in glob.glob(os.path.join (workspace, RemotePath[remote], path), recursive=False):
    Path.append (os.path.realpath (p))
  return Path

def GetCodePath (workspace, manifest):
  Path = []
  Manifest = ET.parse (manifest).getroot ()
  for SparseData in Manifest.findall ("./SparseCheckout/SparseData"):
    try:
      Remote = SparseData.attrib["remote"]
    except:
      Remote = None

    for Includes in SparseData.findall ("./AlwaysInclude"):
      for Include in Includes.text.split("|"):
        Path = Path + ConvertPath (workspace, Remote, Include)
  return Path

def InDirectory(child, directory):
  #make both absolute    
  directory = os.path.join(directory, '') # add trailing "\\"
  if os.path.isdir (child):
    child = os.path.join (child, "")

  #return true, if the common prefix of both is equal to directory
  #e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
  return os.path.commonprefix([child, directory]) == directory

parser = argparse.ArgumentParser ()
parser.add_argument ("-o", "--output", help="output paths to a file", type=str)
parser.add_argument ("-v", "--verbose", help="verbose", action="store_true")
parser.add_argument ("project", help="project name", type=str, nargs="+")
parser.add_argument ("-w", "--workspace", help="path to work space", type=str, required=True)
args = parser.parse_args ()

CiXmlRoot = r"C:\ProgramData\edkrepo\cr-manifest-master\\"
CiIndex = r"CiIndex.xml"

CodePath = []

# collect project code path from CR manifest
for p in ET.parse (CiXmlRoot + CiIndex).getroot ():
  if p.attrib["name"] in args.project:
    CodePath = CodePath + GetCodePath (args.workspace, CiXmlRoot + p.attrib["xmlPath"])

# remove duplicated paths (including child path)
CodePath = list (dict.fromkeys (CodePath))
CodePath2 = []
for child in CodePath:
  Add = True
  for parent in CodePath:
    if not os.path.isdir (parent):
      continue
    if child == parent:
      continue
    if InDirectory (child, parent):
      if args.verbose:
        print (f"Remove {child} since {parent} exists.")
      Add = False
      break
  if Add and child not in CodePath2:
    CodePath2.append (child)

# use realpath() to match the path in the file system.
# 1. e:\work --> E:\Work
# 2. E:\\Work --> E:\Work
CodePath = [os.path.realpath(p) for p in CodePath2]
CodePath.sort ()

if args.output is not None:
  with open (args.output, "w+") as f:
    for p in CodePath:
      f.write (p + "\n")
else:
  for p in CodePath:
    print(p)