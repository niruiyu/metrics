import os
import os.path
import glob
import sys
import xml.etree.ElementTree as ET
import argparse
import re

FILE_TYPE = [".c", "ec", "pgc", "act", ".cc", ".cpp", ".cxx", ".c++", ".pcc", ".h", "hh", ".hpp", ".hxx"]
CPD_XML = "cpd.xml"

def InDirectory(child, directory):
  #make both absolute    
  directory = os.path.join(directory, '') # add trailing "\\"
  if os.path.isdir (child):
    child = os.path.join (child, "")

  #return true, if the common prefix of both is equal to directory
  #e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
  return os.path.commonprefix([child, directory]) == directory

def CountLocFast (path, exclude = []):
  Loc = 0
  LocCmd = f"loc {path}"
  for ex in exclude:
    LocCmd = LocCmd + " --exclude " + re.escape (os.path.realpath (ex))
  os.system (f"{LocCmd} > loc.txt")
  for line in open ("loc.txt", "r"):
    array = line.split ()
    if array[0] in ["C", "C++"]:
      Loc = Loc + int (array[2])
    if array[0] == "C/C++" and array[1] == "Header":
      Loc = Loc + int (array[3])
  return Loc

def _CountLoc (path, exclude):
  TotalLoc = 0

  for ex in exclude:
    if path == ex:
      return 0
    if os.path.isdir (ex):
      if InDirectory (path, ex):
        return 0

  if os.path.isfile (path):
    if os.path.splitext (path)[1].lower() in FILE_TYPE:
      return sum(1 for Lines in open(path, encoding='ISO-8859-1'))
    else:
      return 0

  if os.path.isdir (path):
    for File in glob.glob(path + r'\**', recursive=True):
        if not os.path.isfile(File):
            continue
        TotalLoc = TotalLoc + _CountLoc (File, exclude)

    return TotalLoc

def CountLoc (path, exclude):
  TotalLoc = 0

  for p in path.split():
    TotalLoc = TotalLoc + _CountLoc (p, exclude)
  return TotalLoc

parser = argparse.ArgumentParser ()
parser.add_argument ("-fl", "--filelist", help="Path to a file containing a list of files to analyze.", type=str)
parser.add_argument ("-f", "--file", help="File to analyze.", type=str, nargs="*")
parser.add_argument ("-v", "--verbose", help="verbose", action="store_true")
parser.add_argument ("--tokens", help="The minimum token length which should be reported as a duplicate.", default=100, type=int)
parser.add_argument ("-el", "--excludelist", help="Path to a file containing a list of files NOT to analyze.", type=str)
parser.add_argument ("-e", "--exclude", help="File NOT to analyze", type=str, nargs="*")
args = parser.parse_args ()

if args.file is not None:
  CodePath = [os.path.realpath(f) for f in args.file]
else:
  CodePath = []
if args.filelist is not None:
  for p in open (args.filelist, "r"):
    CodePath.append (os.path.realpath (p.rstrip ("\r\n")))

if args.exclude is not None:
  Exclude = [os.path.realpath(ex) for ex in args.exclude]
else:
  Exclude = []
if args.excludelist is not None:
  for p in open (args.excludelist, "r"):
    Exclude.append (os.path.realpath (p.rstrip ("\r\n")))

# Detect code clone
print ("run CPD...")
CpdCmdLine = r'E:\bin\pmd-bin-6.24.0\bin\cpd.bat --minimum-tokens {0} --format xml --language c --encoding ISO-8859-1'.format (args.tokens)
for p in CodePath:
  CpdCmdLine = CpdCmdLine + f" --files {p}"

for p in Exclude:
  CpdCmdLine = CpdCmdLine + f" --exclude {p}"

print (CpdCmdLine)
os.system (f"{CpdCmdLine} > {CPD_XML}")

# Count LOC
print ("count LOC...")
TotalLoc = CountLocFast (str.join (" ", CodePath), Exclude)
#TotalLoc2 = CountLoc (str.join (" ", CodePath), Exclude)

tree = ET.parse (CPD_XML)
root = tree.getroot ()

#   <duplication lines="204" tokens="608">
#      <file column="57" endcolumn="1" endline="1423" line="1220"
#            path="E:\work\edk2\ArmVirtPkg\Library\BaseCachingPciExpressLib\PciExpressLib.c"/>
#      <file column="57" endcolumn="1" endline="1413" line="1210"
#            path="E:\work\edk2\MdePkg\Library\BasePciExpressLib\PciExpressLib.c"/>
#      <file column="32" endcolumn="1" endline="1424" line="1214"
#            path="E:\work\edk2\MdePkg\Library\SmmPciExpressLib\PciExpressLib.c"/>
#      <codefragment>

LineDb = {}
DuplicateLoc = 0

for duplication in root.findall ("./duplication"):
  # Because the next for-loop will count all the duplicated lines in DuplicateLoc,
  # substract one necessary instance of the duplication.
  DuplicateLoc = DuplicateLoc - int (duplication.attrib["lines"], 10)
  Files = duplication.findall ("./file")
  
  for file in Files:
    Path = file.attrib["path"]
    Start = int (file.attrib["line"], 10)
    End = int (file.attrib["endline"], 10)
    if os.path.splitext (Path)[1].lower () not in FILE_TYPE:
      print (Path)
    
    try:
      LineDb[Path].append ((Start, End))
    except:
      LineDb[Path] = [(Start, End)]

for path in LineDb:
  LineDb[path].sort (key=lambda x: x[0])
  Start = -1
  for (s, e) in LineDb[path]:
    if Start == -1:
      Start = s
      End = e
    
    if s > End:
      # no overlap
      DuplicateLoc = DuplicateLoc + End + 1 - Start
      Start = s
      End = e
    elif s <= End:
      # overlap, extend End
      End = max (End, e)

  if Start != -1:
    DuplicateLoc = DuplicateLoc + End + 1 - Start

print (f"Duplicate LOC = {DuplicateLoc}")
print (f"Total LOC = {TotalLoc}")
print ("Duplication/Total = {0:.3f}".format (DuplicateLoc/TotalLoc))
