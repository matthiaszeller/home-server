import logging

from dotenv import load_dotenv
from providers.cloudflare import CloudFlareDNSProvider
from providers.duckdns import DuckDNSProvider

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info(f"loaded dotenv: {load_dotenv()}")

    CloudFlareDNSProvider().run()
    DuckDNSProvider().run()
