import json
import flywheel

# logging stuff
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('fw-heudiconv-gear')
logger.info("=======: fw-heudiconv starting up :=======")

# start up inputs
invocation = json.loads(open('config.json').read())
config = invocation['config']
inputs = invocation['inputs']
destination = invocation['destination']

fw = flywheel.Flywheel(inputs['api_key']['key'])
user = fw.get_current_user()

# start up logic:
heuristic = None #inputs['heuristic']['location']['path']
analysis_container = fw.get(destination['id'])
project_container = fw.get(analysis_container.parents['project'])
project_label = project_container.label
dry_run = False #config['dry_run']
action = "Export" #config['action']
use_all_sessions = config['use_all_sessions']

if use_all_sessions:
