from utils import SysArgs
from nidac import Nidac

nida = Nidac(file_path=SysArgs.file)
nida.compile()
