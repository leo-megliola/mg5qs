import os

# list required environment variables here
required_vars = ['MG5QS_MG5_PATH', 'MG5QS_PROC_CARD_PATH', 'MG5QS_GEN_EVENT_INPUT_SPEC']

for env in required_vars:
    v = os.getenv(env)
    if v is None:
        raise Exception('Environment variable not set: ' + env)
    for path in v.split(':'):
        if len(path.strip()) > 0 and not os.path.exists(path):
            raise Exception('Path does not exist in ' + env + ':' + path)
    print('OK: ', env)