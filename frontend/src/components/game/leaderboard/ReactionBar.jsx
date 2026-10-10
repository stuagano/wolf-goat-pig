import React from 'react';

export const ROUND_REACTION_EMOJIS = ['🏌️', '😂', '😭', '🔥', '👏', '🤔'];

export default function ReactionBar({ reactions = [], onToggle, canReact, onSignIn }) {
  const used = new Set(reactions.map((reaction) => reaction.emoji));

  return (
    <div className="mt-2 flex flex-wrap items-center gap-1.5">
      {reactions.map((reaction) => (
        <button
          key={reaction.emoji}
          type="button"
          title={reaction.reactor_names.join(', ')}
          aria-pressed={reaction.mine}
          aria-label={`${reaction.emoji} ${reaction.count}`}
          onClick={() => (canReact ? onToggle(reaction.emoji) : onSignIn?.())}
          className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-sm ${
            reaction.mine ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-gray-50'
          }`}
        >
          <span aria-hidden="true">{reaction.emoji}</span>
          <span className="text-xs text-gray-700">{reaction.count}</span>
        </button>
      ))}
      {ROUND_REACTION_EMOJIS.filter((emoji) => !used.has(emoji)).map((emoji) => (
        <button
          key={emoji}
          type="button"
          aria-label={`React ${emoji}`}
          onClick={() => (canReact ? onToggle(emoji) : onSignIn?.())}
          className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-dashed border-gray-300 text-sm text-gray-600 hover:bg-gray-50"
        >
          {emoji}
        </button>
      ))}
    </div>
  );
}
