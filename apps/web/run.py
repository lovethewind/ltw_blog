import sys
from pathlib import Path

import uvicorn

module_path = Path(__file__).parent.parent.parent

if module_path not in sys.path:
    sys.path.append(str(module_path))

from apps.web.core.create_app import create_app

if __name__ == '__main__':
    app = create_app()
    uvicorn.run(app)
