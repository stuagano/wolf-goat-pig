/** Routes a player can open from an email or a shared link without logging in. */

export function isLoginOptionalRoute(pathname) {
  return /^\/game\/[^/]+$/.test(pathname) || /^\/signup\/cancel\/[^/]+$/.test(pathname);
}
