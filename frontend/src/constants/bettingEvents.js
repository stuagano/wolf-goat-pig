// frontend/src/constants/bettingEvents.js
import { v4 as uuidv4 } from 'uuid';

export const BettingEventTypes = {
  DOUBLE_OFFERED: 'DOUBLE_OFFERED',
  DOUBLE_ACCEPTED: 'DOUBLE_ACCEPTED',
  DOUBLE_DECLINED: 'DOUBLE_DECLINED',
  PRESS_OFFERED: 'PRESS_OFFERED',
  PRESS_ACCEPTED: 'PRESS_ACCEPTED',
  PRESS_DECLINED: 'PRESS_DECLINED',
  TEAMS_FORMED: 'TEAMS_FORMED',
  HOLE_COMPLETE: 'HOLE_COMPLETE'
};

export const createBettingEvent = ({ gameId, holeNumber, eventType, actor, data }) => {
  return {
    eventId: uuidv4(),
    gameId,
    holeNumber,
    timestamp: new Date().toISOString(),
    eventType,
    actor,
    data
  };
};

export const isValidEventType = (type) => {
  return Object.values(BettingEventTypes).includes(type);
};
