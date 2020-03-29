#!/usr/bin/env python
"""
Easier to maintain than a bunch of shell regular expressions

Run this to change the manifest so that
"""

with open('manifest.json', 'r') as gcp_manifest_file:
    gcp_manifest = gcp_manifest_file.read()

new_gear_name = gcp_manifest.replace("fmriprep-fwheudiconv", "fmriprep-hpc")
new_gear_source = new_gear_name.replace('"PennBBL"', '"Runs on HPC [Experimental]"')

with open('manifest.json', 'w') as hpc_manifest_file:
    hpc_manifest_file.write(new_gear_source)
