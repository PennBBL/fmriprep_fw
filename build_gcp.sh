# After merging master, run this script to build and upload the hpc-version
IMAGENAME=$(cat manifest.json | grep \"image\": | sed 's/^.*"image": "\(.*\)".*/\1/')
docker build -t ${IMAGENAME} .
fw gear upload
docker push $IMAGENAME
echo "Don't forget to PR the gear exchange"

# Configure the
git checkout hpc
sed -i 's/fmriprep-fwheudiconv:\([^-]\)/fmriprep-fw-hpc:\1/g' manifest.json
IMAGENAME=$(cat manifest.json | grep \"image\": | sed 's/^.*"image": "\(.*\)".*/\1/')
docker build -t ${IMAGENAME} .
docker push ${IMAGENAME}
