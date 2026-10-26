import { useEffect, useState } from 'react';
import { addSyncListener, getQueueOutcome } from '../services/syncManager';

/** Feedback belongs to the submitted draft and exact queue revision, not the
 * current contents of an editor and not a game-wide last-sync timestamp. */
export default function useCorrectionSyncFeedback(draftKey) {
  const [submission, setSubmission] = useState(null);
  const [outcome, setOutcome] = useState(null);

  useEffect(() => {
    if (!submission) return undefined;
    const refresh = () => setOutcome(getQueueOutcome(submission.queueId, submission.queueVersion));
    const unsubscribe = addSyncListener(refresh);
    refresh();
    return unsubscribe;
  }, [submission]);

  const trackQueued = result => {
    setSubmission({ queueId: result.queueId, queueVersion: result.queueVersion, draftKey });
    setOutcome(getQueueOutcome(result.queueId, result.queueVersion));
  };
  const reset = () => { setSubmission(null); setOutcome(null); };

  if (!submission) return { trackQueued, reset, message: null, error: null, submitted: false };
  const changed = submission.draftKey !== draftKey;
  const unsaved = changed ? 'You have unsaved changes. Save to submit this draft.' : '';
  if (outcome?.state === 'rejected') {
    return { trackQueued, reset, submitted: true, message: unsaved || null,
      error: `The submitted correction was rejected: ${outcome.error}. Your edits are still here. Review and retry saving.` };
  }
  let message = unsaved;
  if (!changed) {
    if (outcome?.state === 'synced') message = 'The submitted correction was saved to the server.';
    else if (outcome?.state === 'pending') message = 'Pending sync — not saved to the server yet. The submitted correction is queued on this device.';
    else message = 'The submitted correction is not confirmed. Check sync status or retry saving; it may have been removed or replaced in the queue.';
  }
  return { trackQueued, reset, submitted: true, message, error: null };
}
