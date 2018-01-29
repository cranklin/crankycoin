import logging
import yaml

with open("config/config.yaml", 'r') as ymlfile:
    config = yaml.load(ymlfile)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
