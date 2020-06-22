# ManifestToPaths.py

Extract information from CI manifest to generate file list for given projects.
```
E:\Work\metrics>py -3 ManifestToPaths.py -h
usage: ManifestToPaths.py [-h] [-o OUTPUT] [-v] -w WORKSPACE project [project ...]

positional arguments:
  project               project name

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        output paths to a file
  -v, --verbose         verbose
  -w WORKSPACE, --workspace WORKSPACE
                        path to work space
```

# reuse.py
Invoke PMD/CPD tool and [loc tool](https://github.com/niruiyu/loc.git) to get duplication LOC and total LOC for a given file list.
```
usage: ManifestToPaths.py [-h] [-o OUTPUT] [-v] -w WORKSPACE project [project ...]
ManifestToPaths.py: error: the following arguments are required: project, -w/--workspace

E:\Work\metrics>py -3 ManifestToPaths.py -h
usage: ManifestToPaths.py [-h] [-o OUTPUT] [-v] -w WORKSPACE project [project ...]

positional arguments:
  project               project name

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        output paths to a file
  -v, --verbose         verbose
  -w WORKSPACE, --workspace WORKSPACE
                        path to work space
```

# CountApiRef.py
Calculate API Usage Index for an EDKII library class. It aims to be a metrics to measure API design quality.