// frontend/src/constants/__tests__/bettingEvents.test.js
import { BettingEventTypes, createBettingEvent, isValidEventType } from '../bettingEvents';

describe('BettingEventTypes', () => {
  test('should have all required event types', () => {
    expect(BettingEventTypes.DOUBLE_OFFERED).toBe('DOUBLE_OFFERED');
    expect(BettingEventTypes.DOUBLE_ACCEPTED).toBe('DOUBLE_ACCEPTED');
    expect(BettingEventTypes.DOUBLE_DECLINED).toBe('DOUBLE_DECLINED');
    expect(BettingEventTypes.PRESS_OFFERED).toBe('PRESS_OFFERED');
    expect(BettingEventTypes.PRESS_ACCEPTED).toBe('PRESS_ACCEPTED');
    expect(BettingEventTypes.PRESS_DECLINED).toBe('PRESS_DECLINED');
    expect(BettingEventTypes.TEAMS_FORMED).toBe('TEAMS_FORMED');
    expect(BettingEventTypes.HOLE_COMPLETE).toBe('HOLE_COMPLETE');
  });

  test('should create valid betting event', () => {
    const event = createBettingEvent({
      gameId: 'game-123',
      holeNumber: 5,
      eventType: BettingEventTypes.DOUBLE_OFFERED,
      actor: 'Player1',
      data: { currentMultiplier: 2, proposedMultiplier: 4 }
    });

    expect(event.eventId).toBeDefined();
    expect(event.gameId).toBe('game-123');
    expect(event.holeNumber).toBe(5);
    expect(event.eventType).toBe('DOUBLE_OFFERED');
    expect(event.actor).toBe('Player1');
    expect(event.timestamp).toBeDefined();
    expect(event.data.currentMultiplier).toBe(2);
  });

  test('should validate event types', () => {
    expect(isValidEventType('DOUBLE_OFFERED')).toBe(true);
    expect(isValidEventType('INVALID_TYPE')).toBe(false);
  });
});
