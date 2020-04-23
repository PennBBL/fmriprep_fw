#!/usr/local/miniconda/bin/python
import sys
import logging
from zipfile import ZipFile
from pathlib import PosixPath
from fw_heudiconv.cli import export
import flywheel

# logging stuff
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fmriprep-gear')
logger.info("=======: FMRIPREP :=======")


# Gather variables that will be shared across functions
with flywheel.GearContext() as context:
    # Setup basic logging
    context.init_logging()
    # Log the configuration for this job
    # context.log_config()
    config = context.config
    ignore = config.get('ignore', '').split()
    analysis_id = context.destination['id']
    gear_output_dir = PosixPath(context.output_dir)
    fmriprep_script = gear_output_dir / "fmriprep_run.sh"
    output_root = gear_output_dir / analysis_id
    working_dir = PosixPath(str(output_root.resolve()) + "_work")
    bids_dir = output_root
    bids_root = bids_dir / 'bids_dataset'
    # Get relevant container objects
    fw = flywheel.Client(context.get_input('api_key')['key'])
    analysis_container = fw.get(analysis_id)
    project_container = fw.get(analysis_container.parents['project'])
    session_container = fw.get(analysis_container.parent['id'])
    subject_container = fw.get(session_container.parents['subject'])

    # Flywheel-specific options
    project_label = project_container.label
    extra_t1 = context.get_input('t1_anatomy')
    extra_t1_path = None if extra_t1 is None else \
        PosixPath(context.get_input_path('t1_anatomy'))
    extra_t2 = context.get_input('t2_anatomy')
    extra_t2_path = None if extra_t2 is None else \
        PosixPath(context.get_input_path('t2_anatomy'))
    use_all_sessions = config.get('use_all_sessions', False)



def write_fmriprep_command():
    """Create a command script."""
    with flywheel.GearContext() as context:

        # Mandatory arguments
        cmd = [
            '/usr/local/miniconda/bin/fmriprep',
            '--stop-on-first-crash', '-v', '-v',
            str(bids_root),
            str(output_root),
            'participant',
            '--fs-license-file', context.get_input_path('freesurfer_license'),
            '-w', str(working_dir),
            '--output-spaces', config.get('output_spaces'),
            '--run-uuid', analysis_id]

        # External FreeSurfer Input
        if context.get_input_path("freesurfer_input"):
            cmd += ['--fs-subjects-dir', context.get_input_path("freesurfer_input")]

        # JSON file that contains a file filter
        if context.get_input_path("bids_filter_file"):
            cmd += ['--bids-filter-file', context.get_input_path("bids_filter_file")]

        if config.get('skip_bids_validation'):
            cmd.append('--skip-bids-validation')
        if config.get('task_id'):
            cmd += ['--task-id', config.get('task_id')]
        if config.get('anat_only', False):
            cmd.append('--anat-only')
        if config.get("ignore"):
            cmd += ['--ignore', config.get("ignore")]
        if config.get('longitudinal', False):
            cmd.append('--longitudinal')
        if config.get('t2s_coreg'):
            cmd.append('--t2s-coreg')
        if config.get('bold2t1w_dof'):
            cmd += ['--bold2t1w-dof', str(config.get('bold2t1w_dof'))]
        if config.get('force_bbr'):
            cmd.append('--force-bbr')
        if config.get('force_no_bbr'):
            cmd.append('--force-no-bbr')
        if config.get('dummy_scans'):
            cmd += ['--dummy-scans', str(config.get('dummy_scans'))]

        # Aroma options
        if config.get('use_aroma'):
            cmd.append('--use-aroma')
            if config.get('aroma_melodic_dimensionality'):
                cmd += ['--aroma-melodic-dimensionality',
                        '%d' % config.get('aroma_melodic_dimensionality')]

        # Confounds options
        if config.get('return_all_components'):
            cmd.append('--return-all-components')
        if config.get('fd_spike_threshold'):
            cmd += ['--fd-spike-threshold', str(config.get('fd_spike_threshold'))]
        if config.get('dvars_spike_threshold'):
            cmd += ['--dvars-spike-threshold', str(config.get('dvars_spike_threshold'))]

        # Specific options for ANTs registrations
        if config.get('skull_strip_fixed_seed'):
            cmd.append('--skull-strip-fixed-seed')
        if config.get('skull_strip_template'):
            cmd += ['--skull-strip-template', config.get('skull_strip_template')]

        # Fieldmap options
        if config.get('fmap_bspline', False):
            cmd.append('--fmap-bspline')
        if config.get('fmap_no_demean', False):
            cmd.append('--fmap-no-demean')

        # Specific options for SyN distortion correction
        if config.get('force_syn', False):
            cmd.append('--force-syn')
        if config.get('use_syn_sdc', False):
            cmd.append('--use-syn-sdc')

        # Surface preprocessing options
        if config.get('fs_no_reconall', False):
            cmd.append('--fs-no-reconall')
        if not config.get('cifti_output') == 'None':
            cmd += ['--cifti-output', config.get('cifti_output')]
        if config.get('no_submm_recon'):
            cmd.append('--no-submm-recon')
        if config.get('medial_surface_nan'):
            cmd.append('--medial-surface-nan')

        # If on HPC, get the cores/memory limits
        if config.get('sge-cpu'):
            # Parse SGE cpu syntax, such as "4-8" or just "4"
            cpuMin = int(config.get('sge-cpu').split('-')[0])
            cmd += ['--nthreads', str(max(1, cpuMin - 1))]

        if config.get('notrack'):
            cmd.append('--notrack')
        if config.get('sloppy', False):
            cmd.append('--sloppy')

    logger.info(' '.join(cmd))
    with fmriprep_script.open('w') as f:
        f.write(' '.join(cmd))

    return fmriprep_script.exists()


def get_external_bids(scan_info, local_file):
    """Download an external T1 or T2 image.

    Query flywheel to find the correct acquisition and get its BIDS
    info. scan_info came from context.get_input('*_anatomy').
    """
    modality = scan_info['object']['modality']
    logger.info("Adding additional %s folder...", modality)
    external_acq = fw.get(scan_info['hierarchy']['id'])
    external_niftis = [f for f in external_acq.files if
                       f.name == scan_info['location']['name']]
    if not len(external_niftis) == 1:
        raise Exception("Unable to find location for extra %s" % modality)
    nifti = external_niftis[0]
    nifti_bids_path = bids_root / nifti.info['BIDS']['Path']
    json_bids_path = str(nifti_bids_path).replace(
        "nii.gz", ".json").replace(".nii", ".json")
    # Warn if overwriting: Should never happen on purpose
    if nifti_bids_path.exists():
        logger.warning("Overwriting current T1w image...")
    # Copy to / overwrite its place in BIDS
    local_file.replace(nifti_bids_path)

    # Download the sidecar
    export.download_sidecar(nifti.info, json_bids_path)
    assert PosixPath(json_bids_path).exists()
    assert nifti_bids_path.exists()


def fw_heudiconv_download():
    """Use fw-heudiconv to download BIDS data.

    Returns True if success or False if there are no dwi files."""
    subjects = [subject_container.label]
    if not use_all_sessions:
        # find session object origin
        sessions = [session_container.label]
    else:
        sessions = None

    # Do the download!
    bids_root.parent.mkdir(parents=True, exist_ok=True)
    downloads = export.gather_bids(fw, project_label, subjects, sessions)
    export.download_bids(fw, downloads, str(bids_dir.resolve()), dry_run=False)

    # Download the extra T1w or T2w
    if extra_t1 is not None:
        get_external_bids(extra_t1, extra_t1_path)
    if extra_t2 is not None:
        get_external_bids(extra_t2, extra_t2_path)

    bold_files = [fname for fname in bids_root.glob("**/*") if "func/" in str(fname)]
    if not len(bold_files):
        logger.warning("No BOLD files found in %s", bids_root)
    return True


def main():

    download_ok = fw_heudiconv_download()
    sys.stdout.flush()
    sys.stderr.flush()
    if not download_ok:
        logger.warning("Critical error while trying to download BIDS data.")
        return 1

    command_ok = write_fmriprep_command()
    sys.stdout.flush()
    sys.stderr.flush()
    if not command_ok:
        logger.warning("Critical error while trying to write fmriprep command.")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
