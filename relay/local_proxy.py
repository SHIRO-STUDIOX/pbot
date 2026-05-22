import os
import sys
import base64
import logging
import asyncio
from aiohttp import web, ClientSession, ClientTimeout

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s [%(name)s] - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("relay.proxy")

# 1. Load Configurations from environment variables
GAS_URL = os.getenv("GAS_URL", "")
RELAY_TOKEN = os.getenv("RELAY_TOKEN", "")
PROXY_PORT = int(os.getenv("PROXY_PORT", "8080"))
PROXY_HOST = os.getenv("PROXY_HOST", "0.0.0.0")

# Validation
if not GAS_URL:
    logger.error("WARNING: GAS_URL environment variable is not set! Proxy will fail to relay requests.")
if not RELAY_TOKEN:
    logger.error("WARNING: RELAY_TOKEN environment variable is not set! Requests will likely be rejected by GAS.")

async def handle_relay(request: web.Request) -> web.StreamResponse:
    """
    Captures incoming Telegram API request, packages it with security token,
    relays it to Google Apps Script, and returns the response.
    """
    target_path = request.path
    query_string = request.query_string
    target_url = f"https://api.telegram.org{target_path}"
    if query_string:
        target_url += f"?{query_string}"

    logger.info("Intercepted request: %s %s -> Relaying...", request.method, target_path)

    # 1. Read raw body and encode to Base64
    raw_body = await request.read()
    body_base64 = ""
    if raw_body:
        body_base64 = base64.b64encode(raw_body).decode("utf-8")

    # 2. Reconstruct headers (exclude specific server-to-server hop headers)
    exclude_headers = {"host", "connection", "content-length", "content-encoding"}
    client_headers = {
        key: val for key, val in request.headers.items() 
        if key.lower() not in exclude_headers
    }

    # 3. Create JSON payload for Google Apps Script
    payload = {
        "token": RELAY_TOKEN,
        "targetUrl": target_url,
        "method": request.method,
        "headers": client_headers,
        "body_base64": body_base64
    }

    # 4. Post request to Google Apps Script
    timeout = ClientTimeout(total=60.0) # Telegram calls can occasionally be slow
    try:
      async with ClientSession(timeout=timeout) as session:
          async with session.post(GAS_URL, json=payload) as response:
              if response.status != 200:
                  error_text = await response.text()
                  logger.error("Google Apps Script returned HTTP %s: %s", response.status, error_text)
                  return web.json_response({"error": "GAS server returned error status", "details": error_text}, status=502)

              result = await response.json()

              # Handle application-level failures from the GAS script itself
              if "error" in result:
                  logger.error("Relay failed: %s (%s)", result["error"], result.get("details", ""))
                  return web.json_response(result, status=502)

              # 5. Extract response metadata and decode body
              resp_status = result.get("status", 200)
              resp_headers = result.get("headers", {})
              resp_body_base64 = result.get("body_base64", "")

              resp_bytes = b""
              if resp_body_base64:
                  resp_bytes = base64.b64decode(resp_body_base64)

              # Filter returned headers to avoid duplication or transfer bugs
              filtered_headers = {}
              for k, v in resp_headers.items():
                  if k.lower() not in {"content-length", "transfer-encoding", "content-encoding", "connection"}:
                      filtered_headers[k] = str(v)

              logger.info("Successfully relaid %s %s. Response status: %s", request.method, target_path, resp_status)
              return web.Response(body=resp_bytes, status=resp_status, headers=filtered_headers)

    except asyncio.TimeoutError:
        logger.error("Timeout occurred while relaying to GAS.")
        return web.json_response({"error": "Gateway Timeout while contacting GAS"}, status=504)
    except Exception as e:
        logger.exception("Unexpected exception occurred during relay:")
        return web.json_response({"error": "Internal Proxy Error", "details": str(e)}, status=500)

def main():
    logger.info("Initializing Local Telegram API Proxy server...")
    logger.info("GAS Endpoint URL: %s", GAS_URL)
    logger.info("Listening on: http://%s:%s", PROXY_HOST, PROXY_PORT)

    app = web.Application()
    # Route all requests to our handler
    app.router.add_route("*", "/{tail:.*}", handle_relay)

    try:
        web.run_app(app, host=PROXY_HOST, port=PROXY_PORT, access_log=None)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Proxy server stopped by shutdown signal.")

if __name__ == "__main__":
    main()
