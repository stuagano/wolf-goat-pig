const toBoolean = (value) => {
  if (typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'string') {
    return ['true', '1', 'yes', 'on'].includes(value.trim().toLowerCase());
  }
  if (typeof value === 'number') {
    return value === 1;
  }
  return false;
};

export const simulationConfig = {
  apiUrl: process.env.REACT_APP_API_URL || '',
  useMocks: toBoolean(process.env.REACT_APP_SIMULATION_USE_MOCKS),
  mockPreset: process.env.REACT_APP_SIMULATION_MOCK_PRESET || 'default',
};

export default {
  simulation: simulationConfig,
};
