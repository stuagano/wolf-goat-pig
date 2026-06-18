// Shared admin-access helpers.
//
// IMPORTANT: there is intentionally NO hardcoded fallback email here.
// An unauthenticated visitor must never be silently treated as an admin.
// The backend independently validates X-Admin-Email via ADMIN_EMAILS.

export const ADMIN_EMAILS = ['stuagano@gmail.com', 'admin@wgp.com'];

/** Email stored by Navigation after Auth0 login; empty string if not logged in. */
export const getStoredUserEmail = () => localStorage.getItem('userEmail') || '';

export const isAdminEmail = (email) => !!email && ADMIN_EMAILS.includes(email);

/** Header object for admin-gated backend endpoints. */
export const adminHeaders = () => ({ 'X-Admin-Email': getStoredUserEmail() });
