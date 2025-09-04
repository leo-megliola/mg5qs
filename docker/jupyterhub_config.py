import os
import nativeauthenticator
import pwd
import shutil
import subprocess
from pathlib import Path

c = get_config()

# use NativeAuthenticator to allow anonyumous sign-up and account creation
c.JupyterHub.authenticator_class = 'nativeauthenticator.NativeAuthenticator'
c.JupyterHub.template_paths = [f'{os.path.dirname(nativeauthenticator.__file__)}/templates/']
c.NativeAuthenticator.open_signup = True
c.Authenticator.allow_all = True

# hub binding
c.JupyterHub.bind_url = 'http://0.0.0.0:8000'
c.JupyterHub.trusted_downstream_ips = ['127.0.0.1']

# persistent storage
c.JupyterHub.cookie_secret_file = '/etc/jupyterhub/jupyterhub_cookie_secret'
c.JupyterHub.db_url = 'sqlite:////etc/jupyterhub/jupyterhub.sqlite'

# environment setup for all users
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
    base_env['PYTHONPATH'] = f'/opt/mg5qs/python:/opt/mg5qs/lib:{existing}'
else:
    base_env['PYTHONPATH'] = '/opt/mg5qs/python:/opt/mg5qs/lib'

c.Spawner.environment = base_env.copy()

def pre_spawn(spawner):
    username = spawner.user.name
    user_home = Path(f'/home/{username}')

    # check if user exists, create if not
    try:
        pw = pwd.getpwnam(username)
        spawner.log.info(f'System user {username} already exists')
    except KeyError:
        # user doesn't exist...
        spawner.log.info(f'Creating system user {username}...')
        try:
            subprocess.run([
                'adduser',
                '--home', str(user_home),
                '--shell', '/bin/bash',
                '--gecos', '',
                '--disabled-password',
                username
            ], check=True, capture_output=True, text=True)
            spawner.log.info(f'Successfully created system user {username}')
            pw = pwd.getpwnam(username)
        except subprocess.CalledProcessError as e:
            spawner.log.error(f'Failed to create system user {username}: {e}')
            spawner.log.error(f'Command output: {e.stdout}')
            spawner.log.error(f'Command error: {e.stderr}')
            raise

    uid, gid = pw.pw_uid, pw.pw_gid

    # this process runs as root, so any user directories or files need 'chown' root->user
    
    # check if home directory exists
    if not user_home.exists():
        user_home.mkdir(mode=0o755, parents=True)
        os.chown(user_home, uid, gid)
        spawner.log.info(f'Created and set ownership of {user_home}')

    stat_result = user_home.stat()
    if stat_result.st_uid != uid or stat_result.st_gid != gid:
        spawner.log.info(f'Fixing ownership of home directory {user_home}...')
        os.chown(user_home, uid, gid)

    # create MadGraph directory
    user_mg5_dir = user_home / 'mg5amcnlo'
    if not user_mg5_dir.exists():
        try:
            spawner.log.info(f'Copying MadGraph for user {username}...')
            shutil.copytree('/opt/madgraph', user_mg5_dir, symlinks=True, ignore_dangling_symlinks=True)
            spawner.log.info(f'MadGraph copied to {user_mg5_dir}')
            # Use subprocess to change ownership recursively, as the copy was done by root
            spawner.log.info(f'Changing ownership of {user_mg5_dir} to user {uid}...')
            subprocess.run(['chown', '-R', f'{uid}:{gid}', str(user_mg5_dir)], check=True)
        except subprocess.CalledProcessError as e:
            spawner.log.error(f'Failed to change ownership of {user_mg5_dir}: {e.stderr}')
            # Clean up the failed copy
            if user_mg5_dir.exists():
                shutil.rmtree(user_mg5_dir)
            raise
        except Exception as e:
            spawner.log.error(f'Failed to copy MadGraph for {username}: {e}')
            raise

    # create example input files
    user_input_dir = user_home / 'input'
    if not user_input_dir.exists():
        try:
            spawner.log.info(f'Copying input files for user {username}...')

            def ignore_non_dat(dir, files):
                # keep only files that end with .dat
                return [f for f in files if not f.endswith('.dat')]

            shutil.copytree("/opt/mg5qs/docker", user_input_dir, ignore=ignore_non_dat)

            spawner.log.info(f'input files copied to {user_input_dir}')

            # Use subprocess to change ownership recursively, as the copy was done by root
            spawner.log.info(f'Changing ownership of {user_input_dir} to user {uid}...')
            subprocess.run(['chown', '-R', f'{uid}:{gid}', str(user_input_dir)], check=True)

        except subprocess.CalledProcessError as e:
            spawner.log.error(f'Failed to change ownership of {user_input_dir}: {e.stderr}')
            # Clean up the failed copy
            if user_input_dir.exists():
                shutil.rmtree(user_input_dir)
            raise
        except Exception as e:
            spawner.log.error(f'Failed to copy input files for {username}: {e}')
            raise

    try:
        spawner.log.info(f'Copying example notebooks for user {username}...')

        def ignore_non_ipynb(dirpath, entries):
            # Keep only files ending in .ipynb; ignore everything else
            return [name for name in entries if not name.endswith('.ipynb')]

        # Copy from the source directory; ignore everything that's not *.ipynb.
        # dirs_exist_ok=True allows copying into an existing home directory.
        shutil.copytree(
            "/opt/mg5qs/docker",
            user_home,
            ignore=ignore_non_ipynb,
            dirs_exist_ok=True
        )

        spawner.log.info(f'Example notebooks copied to {user_home}')

        # Fix ownership since the copy likely ran as root
        spawner.log.info(f'Changing ownership of {user_home} to user {uid}...')
        subprocess.run(['chown', '-R', f'{uid}:{gid}', str(user_home)], check=True)

    except subprocess.CalledProcessError as e:
        spawner.log.error(f'Failed to change ownership of {user_home}: {e.stderr}')
        # Do NOT remove the entire home directory; just re-raise.
        raise
    except Exception as e:
        spawner.log.error(f'Failed to copy example notebooks for {username}: {e}')
        raise

    
    
    #========================================================================

    # set MG5AMCNLO env to point to user's copy
    spawner.environment['MG5AMCNLO'] = str(user_mg5_dir)

    # extend LD_LIBRARY_PATH
    old_path = spawner.environment.get('LD_LIBRARY_PATH', '')
    spawner.environment['LD_LIBRARY_PATH'] = f'/opt/pythia8310/lib:{old_path}'
    spawner.environment['PYTHIA8'] = '/opt/pythia8310'
    spawner.environment['PYTHIA8DATA'] = '/opt/pythia8310/share/Pythia8/xmldoc'
    spawner.environment['PYTHIA8_XMLDOC'] = '/opt/pythia8310/share/Pythia8/xmldoc'

    # try enabling widgetsnbextension if jupyter-nbextension exists
    if shutil.which('jupyter-nbextension'):
        try:
            subprocess.run([
                'jupyter-nbextension', 'enable', '--py',
                'widgetsnbextension', '--sys-prefix'
            ], check=True)
        except Exception as e:
            spawner.log.warning(f'pre_spawn: nbextension enable failed: {e}')

# Assign the pre-spawn hook
c.Spawner.pre_spawn_hook = pre_spawn
