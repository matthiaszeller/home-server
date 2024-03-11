

from common.config import setup
setup(__file__)
from src.rest_api import *


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, ssl_context='adhoc')
