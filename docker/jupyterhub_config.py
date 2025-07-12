c = get_config()  # noqa

# Auth and PAM login
c.JupyterHub.authenticator_class = 'jupyterhub.auth.PAMAuthenticator'
c.Authenticator.allow_all = True
# c.PAMAuthenticator.service = 'jupyterhub'

# Hub binding
c.JupyterHub.bind_url = 'http://0.0.0.0:8000'
c.JupyterHub.trusted_downstream_ips = ['127.0.0.1']

# Persistent storage
c.JupyterHub.cookie_secret_file = '/etc/jupyterhub/jupyterhub_cookie_secret'
c.JupyterHub.db_url = 'sqlite:////etc/jupyterhub/jupyterhub.sqlite'

# Environment setup for all users
base_env = {
    'MG5AMCNLO': '/opt/madgraph',
    'MG5QS_INPUT_PATH': '/opt/mg5qs/input',
    'PYTHIA8': '/opt/pythia8310',
    'PYTHIA8DATA': '/opt/pythia8310/share/Pythia8/xmldoc',
    'PYTHIA8_XMLDOC': '/opt/pythia8310/share/Pythia8/xmldoc',
    'JUPYTER_ENABLE_LAB': '1',
    'JUPYTER_ENABLE_NBEXTENSIONS': '1'
}

existing = base_env.get('PYTHONPATH')
if existing:
    base_env['PYTHONPATH'] = f"/opt/mg5qs/python:/opt/mg5qs/lib:{existing}"
else:
    base_env['PYTHONPATH'] = "/opt/mg5qs/python:/opt/mg5qs/lib"

c.Spawner.environment = base_env.copy()

def pre_spawn(spawner):
    import shutil
    import subprocess
    from pathlib import Path
    import os

    username = spawner.user.name
    user_home = Path(f"/home/{username}")
    user_mg5_dir = user_home / "mg5_work"

    # Copy MadGraph to user's home if not already present
    if not user_mg5_dir.exists():
        try:
            spawner.log.info(f"Copying MadGraph for user {username}...")
            shutil.copytree("/opt/madgraph", user_mg5_dir)
            spawner.log.info(f"MadGraph copied to {user_mg5_dir}")
        except Exception as e:
            spawner.log.error(f"Failed to copy MadGraph for {username}: {e}")

    import pwd
    uid = pwd.getpwnam(username).pw_uid
    gid = pwd.getpwnam(username).pw_gid

    for root, dirs, files in os.walk(user_mg5_dir):
        for momo in dirs:
            os.chown(os.path.join(root, momo), uid, gid)
        for momo in files:
            os.chown(os.path.join(root, momo), uid, gid)

    # Set MG5AMCNLO env to point to user's copy
    spawner.environment['MG5AMCNLO'] = str(user_mg5_dir)

    # Extend LD_LIBRARY_PATH safely
    old_path = spawner.environment.get('LD_LIBRARY_PATH', '')
    spawner.environment['LD_LIBRARY_PATH'] = f"/opt/pythia8310/lib:{old_path}"
    spawner.environment['PYTHIA8'] = '/opt/pythia8310'
    spawner.environment['PYTHIA8DATA'] = '/opt/pythia8310/share/Pythia8/xmldoc'
    spawner.environment['PYTHIA8_XMLDOC'] = '/opt/pythia8310/share/Pythia8/xmldoc'

    # Try enabling widgetsnbextension if jupyter-nbextension exists
    if shutil.which('jupyter-nbextension'):
        try:
            subprocess.run([
                'jupyter-nbextension', 'enable', '--py',
                'widgetsnbextension', '--sys-prefix'
            ], check=True)
        except Exception as e:
            spawner.log.warn(f"pre_spawn: nbextension enable failed: {e}")

# Assign the pre-spawn hook
c.Spawner.pre_spawn_hook = pre_spawn
