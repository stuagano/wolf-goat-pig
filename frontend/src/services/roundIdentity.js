import { apiConfig } from '../config/api.config';

export async function readRoundResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(typeof data.detail === 'string' ? data.detail : `Round request failed (${response.status})`);
    error.status = response.status;
    throw error;
  }
  return data;
}
export const reviewUrl = (path = '') => `${apiConfig.baseUrl}/round-reconciliation${path}`;
export const formatQuarters = value => value == null ? 'Not recorded' : `${value > 0 ? '+' : ''}${value}`;
