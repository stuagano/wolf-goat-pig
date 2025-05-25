import React, { useEffect, useState } from "react";

function App() {
  const [rules, setRules] = useState([]);

  useEffect(() => {
    fetch("/api/rules")
      .then(res => res.json())
      .then(setRules);
  }, []);

  return (
    <div>
      <h1>Wolf Goat Pig Rules</h1>
      <ul>
        {rules.map(rule => (
          <li key={rule.id}>
            <strong>{rule.title}</strong>: {rule.description}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App; 