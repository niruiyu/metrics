import os
import sys
import glob
import re
import threading
import time
import argparse

FileType = ['.c']

APIRe = {}
API = {}
Module = {}
Lock = threading.Lock()

'''
  Count how many calls to each API from this module.
'''
def CountApiCall (module):
  for c in glob.glob(f"{module}\\**", recursive=True):
    if os.path.isfile (c) and os.path.splitext (c)[1].lower() in ['.c']:
      with open (c, 'r', encoding='ISO-8859-1') as f:
        for line in f:
          line = line.split('//')[0] # chop the single-line comments
          for api in API:
            if APIRe[api].search (line):
              Lock.acquire ()
              try:
                API[api][module] = API[api][module] + 1
              except:
                API[api][module] = 1
              Lock.release ()


def Main(workspace, library, searchresult, module):
  # 1. collect all APIs from a lib header file
  # 2. get all module INF paths from VS code search result
  EfiApi = False
  # 1. collect all APIs from a lib header file
  #EFIAPI
  reEfiApi = re.compile (r'^\s*EFIAPI\s*$')

  #GetLocalApicBaseAddress (
  reApi = re.compile (r'^\s*([A-Za-z_][\w]*)\s*\(\s*$')
  with open (library, 'r') as f:
    for line in f:
      line = line.split("//")[0]
      if reEfiApi.match (line) is not None:
        EfiApi = True
      else:
        m = reApi.match (line)

        if m is not None and EfiApi:
          api = m.group(1)
          API[api] = {}
          APIRe[api] = re.compile (f"\\b{api}\\b")
          
          if not EfiApi:
            print ('WARNING: Missing EFIAPI for {0}'.format (m.group(1)))

        EfiApi = False


  # 2. get all modules from VS code search result

  # IntelFsp2WrapperPkg\Library\SecFspWrapperPlatformSecLibSample\SecFspWrapperPlatformSecLibSample.inf:
  reInfPath = re.compile (r'^(?:([\w]+)\s+â\x80¢\s+)?([\w\\]+\w[.]inf):$')
  with open (searchresult, 'r', encoding='ISO-8859-1') as f:
    for line in f:
      #line = line.rstrip ("\r\n")
      m = reInfPath.match (line)
      if m is not None:
        # Module -> { API -> # }
        if m.group(1) is not None:
          Module[os.path.join (workspace, m.group (1), os.path.dirname (m.group (2)))] = []
        else:
          Module[os.path.join (workspace, os.path.dirname (m.group (2)))] = []

  # 3. for each module
  #      for each API
  #        If the API is called
  #          Api_RefByModule++;
  Threads = []
  for m in Module:
    t = threading.Thread (target=CountApiCall, args=(m,))
    t.start ()
    Threads.append (t)
    
  for t in Threads:
    t.join () 

  ApiCallCount = 0

  for api in API:
    if len(API[api]) == 0:
      print (f"{api} is NOT called by any module!!")

    ApiCallCount = ApiCallCount + len(API[api])


  # API Usage Index
  print ("------------------------------------------");
  print ("API Usage Index = {0:.3f}".format (ApiCallCount / (len(API) * len (Module))))

  for api in API:
    if module is not None:
      for m in API[api]:
        if m.find (module) != -1:
          print (f"{api} is called by {m}: {API[api][m]}")
  return 0

start = time.time ()

parser = argparse.ArgumentParser ()
parser.add_argument ("-l", "--library", help="Path to the library header file.", type=str, required=True)
parser.add_argument ("-s", "--searchresult", help="Search result from VS Code.", type=str, required=True)
parser.add_argument ("-w", "--workspace", help="path to work space", type=str, required=True)
parser.add_argument ("-m", "--module", help="Show APIs called from the specific module.", type=str)
args = parser.parse_args ()


Main(args.workspace, args.library, args.searchresult, args.module)
print ("Time: {0:.2f}s".format (time.time () - start))
