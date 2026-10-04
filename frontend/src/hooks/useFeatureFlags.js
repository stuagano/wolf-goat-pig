import { useState, useEffect, useContext, createContext, createElement } from 'react';
import { apiConfig } from '../config/api.config';
import { FEATURE_DEFAULTS } from '../config/features';

const FeaturesContext = createContext(FEATURE_DEFAULTS);

export function FeaturesProvider({ children }) {
  const [flags, setFlags] = useState(FEATURE_DEFAULTS);

  useEffect(() => {
    fetch(`${apiConfig.baseUrl}/config/features`)
      .then((r) => r.json())
      .then((data) => {
        if (data?.features) setFlags({ ...FEATURE_DEFAULTS, ...data.features });
      })
      .catch(() => {}); // fall back to defaults silently
  }, []);

  return createElement(FeaturesContext.Provider, { value: flags }, children);
}

export function useFeatureFlags() {
  return useContext(FeaturesContext);
}
