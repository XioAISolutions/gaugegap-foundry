from pathlib import Path

import numpy as np


Path("/tmp").mkdir(parents=True, exist_ok=True)
np.save("/tmp/id.npy", np.diag([1.0, 2.0, 3.0, 4.0]))
