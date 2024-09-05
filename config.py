import os

# list of required env variables for runtime env; addational requirements for dev in README
required_vars = ['MG5QS_MG5_PATH', 'MG5QS_INPUT_PATH']

for env in required_vars:
    v = os.getenv(env)
    if v is None:
        raise Exception('Environment variable not set: ' + env + '\n Please add the environment verrables specified in the README to .bashrc.')
    for path in v.split(':'):
        if len(path.strip()) > 0 and not os.path.exists(path):
            raise Exception('Path does not exist in ' + env + ':' + path)
    print('OK: ', env)