import os
import subprocess
import sys
import glob
import re

FileType = ['.c']

WORK_SPACE = r"E:\Work\edk2\\"

#EFIAPI
reEfiApi = re.compile (r'^\s*EFIAPI\s*$')

#GetLocalApicBaseAddress (
reApi = re.compile (r'^\s*([A-Za-z_][\w]*)\s*\(\s*$')

# IntelFsp2WrapperPkg\Library\SecFspWrapperPlatformSecLibSample\SecFspWrapperPlatformSecLibSample.inf:
reInfPath = re.compile (r'^([\w\\]+\w[.]inf):')

def Main():
  # 1. collect all APIs from a lib header file
  # 2. get all module INF paths from VS code search result
  APIRe = {}
  API = {}
  Module = {}
  EfiApi = False
  (LibH, SearchResult) = (sys.argv[1], sys.argv[2])

  # 1. collect all APIs from a lib header file
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
  for m in Module:
    for c in glob.glob(f"{WORK_SPACE}{m}\\**", recursive=True):
      if os.path.isfile (c) and os.path.splitext (c)[1].lower() in ['.c']:
        with open (c, 'r') as f:
          for line in f:
            line = line.split('//')[0] # chop the single-line comments
            for api in API:
              if APIRe[api].search (line):
                try:
                  API[api][m] = API[api][m] + 1
                except:
                  API[api][m] = 1
    
  
  ApiCallCount = 0

  for api in API:
    if len(API[api]) == 0:
      print (f"{api} is NOT called by any module!!")

    ApiCallCount = ApiCallCount + len(API[api])

  # API Usage Index
  print ("API Usage Index = {0:.3f}".format (ApiCallCount / (len(API) * len (Module))))

  return 0

sys.exit(Main())
