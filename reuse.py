import os
import glob
import sys
import xml.etree.ElementTree as ET

def CountLoc2 (path):
  Loc = 0
  os.system (F"loc {path} > loc.txt")
  for line in open ("loc.txt", "r"):
    array = line.split ()
    if array[0] == "C":
      Loc = Loc + int (array[2])
    if array[0] == "C/C++" and array[1] == "Header":
      Loc = Loc + int (array[3])
  return Loc

def CountLoc (path):
  TotalLoc = 0

  if os.path.isfile (path):
    if os.path.splitext (path)[1].lower() in [".c", ".cpp", ".cxx", ".h", ".hpp", ".hxx"]:
      return sum(1 for Lines in open(path, encoding='ISO-8859-1'))
    else:
      return 0

  if os.path.isdir (path):
    for File in glob.glob(path + r'\**', recursive=True):
        if not os.path.isfile(File):
            continue
        TotalLoc = TotalLoc + CountLoc (File)

    return TotalLoc

def ConvertPath (remote, root, path):
  Path = []
  RemotePath = {
    None : "",
    "IntelRepo": "Intel\\",
    "EdkRepo" : "Edk2\\",
    "Edk2PlatformsRepo" : "Edk2Platforms\\",
    "SvRestrictedRepo" : "SvRestricted\\"
    }
  for p in glob.glob(root + RemotePath[remote] + path, recursive=False):
    Path.append (p)
  return Path

def GetCodePath (manifest):
  Path = []
  Manifest = ET.parse (manifest).getroot ()
  for SparseData in Manifest.findall ("./SparseCheckout/SparseData"):
    try:
      Remote = SparseData.attrib["remote"]
    except:
      Remote = None

    for Includes in SparseData.findall ("./AlwaysInclude"):
      for Include in Includes.text.split("|"):
        Path = Path + ConvertPath (Remote, r"E:\work\Client\\", Include)
  return Path

CiXmlRoot = r"C:\ProgramData\edkrepo\cr-manifest-master\\"
CiIndex = r"CiIndex.xml"

CodePath = []

# collect project code path from CR manifest
for p in ET.parse (CiXmlRoot + CiIndex).getroot ():
  if p.attrib["name"] in sys.argv[1:]:
    CodePath = CodePath + GetCodePath (CiXmlRoot + p.attrib["xmlPath"])

# run CPD
print ("run CPD...")
CpdCmdLine = r'E:\bin\pmd-bin-6.24.0\bin\cpd.bat --minimum-tokens 100 --format xml --language c --encoding ISO-8859-1'
for p in CodePath:
  CpdCmdLine = CpdCmdLine + f" --files {p}"

print (CpdCmdLine)
#os.system (CpdCmdLine + "> output.xml")

# Count LOC
print ("count LOC...")
TotalLoc = CountLoc2 (str.join (" ", CodePath))

tree = ET.parse ("output.xml")
root = tree.getroot ()

#   <duplication lines="204" tokens="608">
#      <file column="57" endcolumn="1" endline="1423" line="1220"
#            path="E:\work\edk2\ArmVirtPkg\Library\BaseCachingPciExpressLib\PciExpressLib.c"/>
#      <file column="57" endcolumn="1" endline="1413" line="1210"
#            path="E:\work\edk2\MdePkg\Library\BasePciExpressLib\PciExpressLib.c"/>
#      <file column="32" endcolumn="1" endline="1424" line="1214"
#            path="E:\work\edk2\MdePkg\Library\SmmPciExpressLib\PciExpressLib.c"/>
#      <codefragment>

DuplicateLoc = 0

for duplication in root.findall ("./duplication"):
  DuplicateLoc = DuplicateLoc + int (duplication.attrib['lines']) * (len (duplication.findall ("file")) - 1)

print (f"Duplicate LOC = {DuplicateLoc}")
print (f"Total LOC = {TotalLoc}")
