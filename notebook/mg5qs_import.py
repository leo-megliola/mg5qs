import sys
from pathlib import Path
import os

# Load environment variables 
MG5_PATH = Path(os.getenv('MG5QS_MG5_PATH'))      
INPUT_PATH = Path(os.getenv('MG5QS_INPUT_PATH'))

notebook_path = Path().resolve()
sys.path.append(str(notebook_path.parent / 'python'))
sys.path.append(str(notebook_path.parent / 'lib'))
from mg5qs_utils import *
from param_card_editor import *
from visual_card_editor import *