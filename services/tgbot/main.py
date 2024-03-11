

from common.config import setup
from src.rest_api import *


if __name__ == '__main__':
    setup(__file__)
    app.run(host='0.0.0.0', debug=False, ssl_context='adhoc')

