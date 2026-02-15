import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Basic Authentication Middleware
 *
 * Protects the entire application with username/password prompt.
 * Credentials are set via environment variables.
 *
 * To bypass auth (for production with proper auth system),
 * set BASIC_AUTH_ENABLED=false
 */
export function middleware(request: NextRequest) {
  // Check if basic auth is enabled (default: true)
  const authEnabled = process.env.BASIC_AUTH_ENABLED !== 'false';

  if (!authEnabled) {
    return NextResponse.next();
  }

  const basicAuth = request.headers.get('authorization');

  if (basicAuth) {
    const authValue = basicAuth.split(' ')[1];
    const [user, pwd] = atob(authValue).split(':');

    // Get credentials from environment variables
    const validUser = process.env.BASIC_AUTH_USER || 'admin';
    const validPassword = process.env.BASIC_AUTH_PASSWORD || 'change-me-in-production';

    if (user === validUser && pwd === validPassword) {
      return NextResponse.next();
    }
  }

  // Request authentication
  return new NextResponse('Authentication required', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="Secure Area"',
    },
  });
}

// Apply middleware to all routes
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization)
     * - favicon.ico (favicon)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
