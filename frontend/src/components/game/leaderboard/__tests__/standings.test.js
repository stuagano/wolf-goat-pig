import { banquetEligible, sortStandings } from '../standings';

const rows = [
  { rank: 2, member: 'Jeff', quarters: 10, rounds: 20, average: 0.5 },
  { rank: 1, member: 'alice', quarters: 40, rounds: 8, average: 5 },
  { rank: 3, member: 'Bob', quarters: -4, rounds: 21, average: -0.2 },
];

test('default rank sort is ascending and uses stored rank', () => {
  expect(sortStandings(rows, 'rank', 'asc').map((r) => r.member)).toEqual(['alice', 'Jeff', 'Bob']);
});

test('each column sorts both directions', () => {
  expect(sortStandings(rows, 'member', 'asc').map((r) => r.member)).toEqual(['alice', 'Bob', 'Jeff']);
  expect(sortStandings(rows, 'quarters', 'desc').map((r) => r.quarters)).toEqual([40, 10, -4]);
  expect(sortStandings(rows, 'rounds', 'asc').map((r) => r.rounds)).toEqual([8, 20, 21]);
  expect(sortStandings(rows, 'average', 'desc').map((r) => r.average)).toEqual([5, 0.5, -0.2]);
});

test('banquet filter keeps 20 or more rounds', () => {
  expect(rows.filter(banquetEligible).map((r) => r.member)).toEqual(['Jeff', 'Bob']);
});
