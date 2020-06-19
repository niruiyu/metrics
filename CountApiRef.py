import os
import sys
import glob
import re
import threading

FileType = ['.c']

WORK_SPACE = r"E:\Work\edk2\\"


APIRe = {}
API = {}
Module = {}
Lock = threading.Lock()

'''
  Count how many calls to each API from this module.
'''
def CountApiCall (module):
  for c in glob.glob(f"{WORK_SPACE}{module}\\**", recursive=True):
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


def Main():
  # 1. collect all APIs from a lib header file
  # 2. get all module INF paths from VS code search result
  EfiApi = False
  (LibH, SearchResult) = (sys.argv[1], sys.argv[2])


  # 1. collect all APIs from a lib header file
  #EFIAPI
  reEfiApi = re.compile (r'^\s*EFIAPI\s*$')

  #GetLocalApicBaseAddress (
  reApi = re.compile (r'^\s*([A-Za-z_][\w]*)\s*\(\s*$')
  with open (LibH, 'r') as f:
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
  reInfPath = re.compile (r'^([\w\\]+\w[.]inf):')
  with open (SearchResult, 'r') as f:
    for line in f:
      m = reInfPath.match (line)
      if m is not None:
        # Module -> { API -> # }
        Module[os.path.dirname (m.group (1))] = []

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
  print ("API Usage Index = {0:.3f}".format (ApiCallCount / (len(API) * len (Module))))

  return 0

import time
start = time.time ()
Main()
print ("Time: {0}".format (time.time () - start))
