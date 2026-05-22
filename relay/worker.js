/**
 * Cloudflare Worker: Telegram API Domain-Fronting Relay
 * 
 * This worker acts as the final hop. It receives requests from Google Apps Script,
 * validates the security token, and forwards the raw request to the official Telegram API.
 */

export default {
  async fetch(request, env, ctx) {
    // Handle CORS preflight requests
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "*",
        }
      });
    }

    // 1. Get Target URL and Security Token from headers
    const targetUrl = request.headers.get("X-Target-Url");
    const relayToken = request.headers.get("X-Relay-Token");

    // Fallback: Check search parameters if headers are not present
    const urlObj = new URL(request.url);
    const finalTargetUrl = targetUrl || urlObj.searchParams.get("targetUrl");
    const finalRelayToken = relayToken || urlObj.searchParams.get("relayToken");

    if (!finalTargetUrl) {
      return new Response(JSON.stringify({ error: "Missing X-Target-Url header or targetUrl parameter" }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }

    // 2. Validate Security Token
    // We fetch the secret RELAY_TOKEN from Worker's environment variables
    const secretToken = env.RELAY_TOKEN || "your_secret_relay_token_here";
    if (finalRelayToken !== secretToken) {
      return new Response(JSON.stringify({ error: "Unauthorized: Invalid Security Token" }), {
        status: 403,
        headers: { "Content-Type": "application/json" }
      });
    }

    // 3. Reconstruct Request Headers (clean up relay metadata headers)
    const clientHeaders = new Headers(request.headers);
    clientHeaders.delete("X-Target-Url");
    clientHeaders.delete("X-Relay-Token");
    clientHeaders.delete("Host"); // Let fetch automatically assign correct Host header

    // 4. Forward the request to Telegram API
    try {
      const isGetOrHead = request.method === "GET" || request.method === "HEAD";
      const forwardOptions = {
        method: request.method,
        headers: clientHeaders,
        body: isGetOrHead ? null : await request.arrayBuffer()
      };

      const response = await fetch(finalTargetUrl, forwardOptions);

      // Reconstruct Response with CORS headers
      const responseHeaders = new Headers(response.headers);
      responseHeaders.set("Access-Control-Allow-Origin", "*");

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: responseHeaders
      });

    } catch (err) {
      return new Response(JSON.stringify({ error: "Relay Fetch Failed", details: err.toString() }), {
        status: 502,
        headers: { "Content-Type": "application/json" }
      });
    }
  }
};
