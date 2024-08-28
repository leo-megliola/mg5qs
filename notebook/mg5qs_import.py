import sys
from pathlib import Path

notebook_path = Path().resolve()
sys.path.append(str(notebook_path.parent / 'python'))
sys.path.append(str(notebook_path.parent / 'lib'))
from mg5qs_utils import *
from param_card_editor import *
from visual_card_editor import *