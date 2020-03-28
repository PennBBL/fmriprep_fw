docker run --rm -ti --entrypoint=/bin/bash \
  -v /Users/mcieslak/projects/upenn/fmriprep_fw/debug/test/fmriprep-fwheudiconv-0.3.1_20.0.5_5e7e7c367204d54a94cfd056/input:/flywheel/v0/input \
  -v /Users/mcieslak/projects/upenn/fmriprep_fw/debug/test/fmriprep-fwheudiconv-0.3.1_20.0.5_5e7e7c367204d54a94cfd056/output:/flywheel/v0/output \
  -v /Users/mcieslak/projects/upenn/fmriprep_fw/debug/test/fmriprep-fwheudiconv-0.3.1_20.0.5_5e7e7c367204d54a94cfd056/config.json:/flywheel/v0/config.json \
  pennbbl/fmriprep-fwheudiconv:0.3.1_20.0.5
