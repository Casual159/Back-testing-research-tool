/**
 * Application Configuration
 *
 * All API calls go through the Next.js proxy (/api/backend/*)
 * which adds auth headers and forwards to the FastAPI backend.
 */

export const config = {
  /**
   * API base URL for frontend requests.
   * Routes through Next.js proxy for auth header injection.
   * The proxy forwards to NEXT_PUBLIC_API_URL (Railway backend).
   */
  apiUrl: '/api/backend',
} as const;

/**
 * Helper function to build API endpoint URLs
 *
 * @example
 * apiEndpoint('/strategies') // => '/api/backend/strategies'
 * apiEndpoint('/data/stats') // => '/api/backend/data/stats'
 */
export function apiEndpoint(path: string): string {
  // Remove leading slash if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;

  // If path already includes api/, strip it (proxy adds /api/ prefix)
  if (cleanPath.startsWith('api/')) {
    return `${config.apiUrl}/${cleanPath.slice(4)}`;
  }

  return `${config.apiUrl}/${cleanPath}`;
}
