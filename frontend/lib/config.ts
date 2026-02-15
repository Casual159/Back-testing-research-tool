/**
 * Application Configuration
 *
 * Environment variables for client-side must start with NEXT_PUBLIC_
 */

export const config = {
  /**
   * Backend API URL
   * - Production: Railway backend URL (set in Vercel environment variables)
   * - Development: Local backend (set in .env.local)
   * - Default: localhost:8000
   */
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
} as const;

/**
 * Helper function to build API endpoint URLs
 *
 * @example
 * apiEndpoint('/strategies') // => 'http://localhost:8000/api/strategies'
 */
export function apiEndpoint(path: string): string {
  // Remove leading slash if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;

  // If path already includes /api, don't add it again
  if (cleanPath.startsWith('api/')) {
    return `${config.apiUrl}/${cleanPath}`;
  }

  return `${config.apiUrl}/api/${cleanPath}`;
}
