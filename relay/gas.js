/**
 * Google Apps Script: Domain-Fronting Proxy
 * 
 * Set this up as a Google Apps Script Web App. It receives requests from the local
 * server, validates the token, and relays them to the Cloudflare Worker.
 * All binary/multipart bodies are transferred as Base64 to prevent encoding issues.
 */

// ⚠️ CONFIGURE THESE VALUES BEFORE DEPLOYMENT
var RELAY_TOKEN = "your_secret_relay_token_here";
var CFW_URL = "https://your-worker.workers.dev"; // Replace with your Cloudflare Worker URL

function doPost(e) {
  try {
    // 1. Parse JSON Payload
    var requestData = JSON.parse(e.postData.contents);
    
    // 2. Validate Security Token
    if (requestData.token !== RELAY_TOKEN) {
      return formatJsonResponse({ error: "Unauthorized: Invalid Security Token" }, 403);
    }
    
    var targetUrl = requestData.targetUrl;
    var method = requestData.method || "POST";
    var headers = requestData.headers || {};
    
    // Decode body from Base64 if present
    var rawBody = null;
    if (requestData.body_base64) {
      rawBody = Utilities.base64Decode(requestData.body_base64);
    }
    
    // 3. Inject Relay Headers for Cloudflare Worker
    headers["X-Target-Url"] = targetUrl;
    headers["X-Relay-Token"] = RELAY_TOKEN;
    
    var options = {
      method: method,
      headers: headers,
      payload: rawBody,
      muteHttpExceptions: true // Capture error status codes instead of throwing
    };
    
    // 4. Relay to Cloudflare Worker
    var response = UrlFetchApp.fetch(CFW_URL, options);
    var responseCode = response.getResponseCode();
    var responseHeaders = response.getHeaders();
    var responseBytes = response.getContent(); // Read response as raw bytes
    
    // Encode response to Base64 to safely handle binary/special character payloads
    var responseBodyBase64 = Utilities.base64Encode(responseBytes);
    
    return formatJsonResponse({
      status: responseCode,
      headers: responseHeaders,
      body_base64: responseBodyBase64
    }, 200);
    
  } catch (err) {
    return formatJsonResponse({
      error: "GAS Relay Failed",
      details: err.toString()
    }, 500);
  }
}

function formatJsonResponse(data, status) {
  var output = ContentService.createTextOutput(JSON.stringify(data));
  output.setMimeType(ContentService.MimeType.JSON);
  return output;
}
