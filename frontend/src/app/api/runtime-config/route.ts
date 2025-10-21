import { NextRequest, NextResponse } from 'next/server'

/**
 * Runtime Configuration Endpoint
 *
 * This endpoint provides server-side environment variables to the client at runtime.
 * This solves the NEXT_PUBLIC_* limitation where variables are baked into the build.
 *
 * Auto-detection logic:
 * 1. If API_URL env var is set, use it (explicit override)
 * 2. Otherwise, detect from incoming HTTP request headers (zero-config)
 * 3. Fallback to localhost:5055 if detection fails
 *
 * This allows the same Docker image to work in different deployment scenarios.
 */
export async function GET(request: NextRequest) {
  // Priority 1: Check if API_URL is explicitly set
  const envApiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL

  if (envApiUrl) {
    return NextResponse.json({
      apiUrl: envApiUrl,
    })
  }

  // Priority 2: Auto-detect from request headers
  try {
    // Get the protocol (http or https)
    // Check X-Forwarded-Proto first (for reverse proxies), then fallback to request scheme
    const proto = request.headers.get('x-forwarded-proto') ||
                  request.nextUrl.protocol.replace(':', '') ||
                  'http'

    // Get the host header (includes port if non-standard)
    const hostHeader = request.headers.get('host')

    if (hostHeader) {
      // Use the same host:port as the incoming request
      // Since nginx proxies everything through 8899, we just return the same URL
      // Ensure port is included (default to 8899 if not present)
      let apiUrl: string
      if (hostHeader.includes(':')) {
        apiUrl = `${proto}://${hostHeader}`
      } else {
        // No port in host header, add 8899
        apiUrl = `${proto}://${hostHeader}:8899`
      }

      console.log(`[runtime-config] Auto-detected API URL: ${apiUrl} (proto=${proto}, host=${hostHeader})`)

      return NextResponse.json({
        apiUrl,
      })
    }
  } catch (error) {
    console.error('[runtime-config] Auto-detection failed:', error)
  }

  // Priority 3: Fallback to localhost:8899 (nginx port)
  console.log('[runtime-config] Using fallback: http://localhost:8899')
  return NextResponse.json({
    apiUrl: 'http://localhost:8899',
  })
}
