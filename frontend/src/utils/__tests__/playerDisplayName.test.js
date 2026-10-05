import { playerDisplayName } from '../playerDisplayName';

test.each([
  [{ legacy_name: 'Kevin Gent', name: 'kevin@example.com' }, { name: 'kevin@example.com' }, 'Kevin Gent'],
  [{ name: 'Casey McFarland' }, { name: 'casey@example.com' }, 'Casey McFarland'],
  [null, { name: 'Casey McFarland' }, 'Casey McFarland'],
  [{ name: 'Unknown Player' }, { name: 'kevin@example.com' }, 'Player'],
  [null, null, 'Player'],
])('prefers the player identity and never substitutes an email as the name', (profile, user, expected) => {
  expect(playerDisplayName(profile, user)).toBe(expected);
});
