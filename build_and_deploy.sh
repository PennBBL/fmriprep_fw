# After merging master, run this script to build and upload the hpc-version
IMAGENAME=$(cat manifest.json | grep \"image\": | sed 's/^.*"image": "\(.*\)".*/\1/')
docker build -t ${IMAGENAME} .
fw gear upload
docker push $IMAGENAME
echo "Don't forget to PR the gear exchange"

# Configure the
git checkout hpc
git merge master 
git checkout --theirs manifest.json
python build_hpc.py
git commit -m 'update hpc'
git push origin hpc
IMAGENAME=$(cat manifest.json | grep \"image\": | sed 's/^.*"image": "\(.*\)".*/\1/')
docker build -t ${IMAGENAME} .
docker push ${IMAGENAME}
