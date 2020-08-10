# third party dependencies
import logging
from contextlib import contextmanager
import pytest
# direct dependencies
from resources.test_support.helpers import resource
from resources.test_support.event_wating import sync_telescope_shutting_down,watchSpec,sync_telescope_starting_up
from resources.test_support.persistance_helping import update_resource_config_file,load_config_from_file
# MVP code
from oet.domain import SKAMid

LOGGER = logging.getLogger(__name__)

# state asserting
def assert_telescope_is_standby():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('OFF')
    resource('mid_csp/elt/master').assert_attribute('State').equals('STANDBY')
    resource('ska_mid/tm_central/central_node').assert_attribute('State').equals('OFF')

def assert_telescope_is_running():
    resource('ska_mid/tm_subarray_node/1').assert_attribute('State').equals('ON')
    resource('mid_csp/elt/master').assert_attribute('State').equals('ON')
    resource('ska_mid/tm_central/central_node').assert_attribute('State').equals('ON')

@contextmanager
def wrap_assertion_as_predicate(predicate: bool):
    try:
        yield
    except:
        predicate = False

# state checkinhg
def is_telescope_standby() -> bool:
    predicate =  True
    with wrap_assertion_as_predicate(predicate):
        assert_telescope_is_standby()
    return predicate

def is_telescope_running() -> bool:
    predicate =  True
    with wrap_assertion_as_predicate(predicate):
        assert_telescope_is_running()
    return predicate

def set_telescope_to_running() -> None:
    # pre conditions
    assert_telescope_is_standby()
    # command
    with sync_telescope_starting_up(LOGGER,timeout=2):
        SKAMid().start_up()


def set_telescope_to_standby() -> None:
    # pre conditions

    # command
    with sync_telescope_shutting_down(LOGGER,timeout=4):
        SKAMid().standby()

## pytest fixtures
ENV_VARS = [
    'HELM_RELEASE',
    'KUBE_NAMESPACE',
    'TANGO_HOST']
RunContext = namedtuple('RunContext', ENV_VARS)

@pytest.fixture(scope="session")
def run_context():
    logging.info('in run_context')
     # list of required environment vars
    values = list()
    
    for var in ENV_VARS:
        assert os.environ.get(var) # all ENV_VARS must have values set
        values.append(os.environ.get(var))

    return RunContext(*values)

class K8_env():
    '''
    An object to help with managing the k8 context in order to 
    ensure tests are not effected by dirty environments
    '''
    def __init__(self, run_context:RunContext ) -> None:
        _, active_context = config.list_kube_config_contexts()
        config.load_kube_config(context=active_context['name'])
        self.v1 = client.CoreV1Api()
        self.extensions_v1_beta1 = client.ExtensionsV1beta1Api()
        self.env = run_context
        self.clean_config_etcd()


    def clean_config_etcd(self) -> None:
        exec_command = [ 'sdpcfg', 'delete', '-R','/'] 
        component_name = 'maintenance-interface'
        namespace = self.env.KUBE_NAMESPACE
        pods = self.v1.list_namespaced_pod(namespace).items
        pod = [p.metadata.name for p in pods if p.metadata.labels.get('component') == component_name]   
        assert len(pod) > 0, f'error in cleaning config db: pod labeled as {component_name} not fpound'
        assert len(pod) < 2, f'error in cleaning config db: duplicate pods labeled as {component_name} foound'
        pod = pod[0]
        resp = stream(self.v1.connect_get_namespaced_pod_exec, 
                pod, 
                namespace, 
                command=exec_command, 
                stderr=True, stdin=False, 
                stdout=True, tty=False)  
        logging.info(f'cleaning configdb:{resp}')


@pytest.fixture(scope='session',autouse=True)
def k8(run_context) -> None:
    '''
    An fixture to help with managing the k8 context in order to 
    ensure tests are not effected by dirty environments
    '''
    logging.info('k8 fixture called')
    yield  K8_env(run_context)
@pytest.fixture
def running_telescope() -> None:
    try:
        set_telescope_to_running()
    except Exception as e:
        if is_telescope_running():
            set_telescope_to_standby()
        raise e
    try:
        yield
        if is_telescope_running():
            set_telescope_to_standby()
    finally:
        pass
        # actions to do irrespective of errors



@pytest.fixture
def resource_config_file() -> str:
    assign_resources_file = 'resources/test_data/TMC_integration/assign_resources1.json'
    update_resource_config_file(assign_resources_file,disable_logging=True)
    config = load_config_from_file(assign_resources_file)
    yield config
