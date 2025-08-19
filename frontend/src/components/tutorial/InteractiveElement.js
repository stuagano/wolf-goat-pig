import React, { useState, useRef, useEffect } from 'react';
import { useTutorial } from '../../context/TutorialContext';
import { useTheme } from '../../theme/Provider';

/**
 * Interactive tutorial elements - quizzes, drag-and-drop, simulations
 */

// Quiz component
export const TutorialQuiz = ({ 
  questionId,
  question,
  options,
  correctAnswer,
  explanation,
  onAnswer
}) => {
  const tutorial = useTutorial();
  const theme = useTheme();
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [answered, setAnswered] = useState(false);

  const handleSubmit = () => {
    if (selectedAnswer === null) return;
    
    const isCorrect = selectedAnswer === correctAnswer;
    tutorial.submitQuizAnswer(questionId, selectedAnswer, isCorrect);
    setShowResult(true);
    setAnswered(true);
    onAnswer && onAnswer(selectedAnswer, isCorrect);
  };

  const resetQuiz = () => {
    setSelectedAnswer(null);
    setShowResult(false);
    setAnswered(false);
  };

  const styles = {
    container: {
      ...theme.cardStyle,
      margin: `${theme.spacing[6]} 0`
    },
    
    question: {
      fontSize: theme.typography.lg,
      fontWeight: theme.typography.semibold,
      marginBottom: theme.spacing[4],
      color: theme.colors.textPrimary
    },
    
    options: {
      display: 'flex',
      flexDirection: 'column',
      gap: theme.spacing[3],
      marginBottom: theme.spacing[4]
    },
    
    option: {
      display: 'flex',
      alignItems: 'center',
      padding: theme.spacing[3],
      borderRadius: theme.borderRadius.base,
      border: `2px solid ${theme.colors.border}`,
      cursor: answered ? 'default' : 'pointer',
      transition: tutorial.reducedMotion ? 'none' : 'all 0.2s ease',
      backgroundColor: theme.colors.paper
    },
    
    optionSelected: {
      borderColor: theme.colors.primary,
      backgroundColor: theme.colors.primaryLight + '20'
    },
    
    optionCorrect: {
      borderColor: theme.colors.success,
      backgroundColor: theme.colors.successLight + '20'
    },
    
    optionIncorrect: {
      borderColor: theme.colors.error,
      backgroundColor: theme.colors.errorLight + '20'
    },
    
    radioButton: {
      marginRight: theme.spacing[3],
      width: 20,
      height: 20
    },
    
    optionText: {
      fontSize: theme.typography.base,
      flex: 1
    },
    
    actions: {
      display: 'flex',
      gap: theme.spacing[3],
      marginBottom: theme.spacing[4]
    },
    
    submitButton: {
      ...theme.buttonStyle,
      opacity: selectedAnswer === null ? 0.6 : 1
    },
    
    retryButton: {
      ...theme.buttonStyle,
      backgroundColor: theme.colors.accent
    },
    
    result: {
      padding: theme.spacing[4],
      borderRadius: theme.borderRadius.base,
      fontSize: theme.typography.base,
      lineHeight: 1.6
    },
    
    resultCorrect: {
      backgroundColor: theme.colors.successLight + '30',
      border: `1px solid ${theme.colors.success}`,
      color: theme.colors.successDark
    },
    
    resultIncorrect: {
      backgroundColor: theme.colors.errorLight + '30',
      border: `1px solid ${theme.colors.error}`,
      color: theme.colors.errorDark
    }
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.question}>{question}</h3>
      
      <div style={styles.options}>
        {options.map((option, index) => {
          let optionStyle = styles.option;
          
          if (showResult) {
            if (index === correctAnswer) {
              optionStyle = { ...optionStyle, ...styles.optionCorrect };
            } else if (index === selectedAnswer && selectedAnswer !== correctAnswer) {
              optionStyle = { ...optionStyle, ...styles.optionIncorrect };
            }
          } else if (selectedAnswer === index) {
            optionStyle = { ...optionStyle, ...styles.optionSelected };
          }
          
          return (
            <div
              key={index}
              style={optionStyle}
              onClick={() => !answered && setSelectedAnswer(index)}
            >
              <input
                type="radio"
                name={questionId}
                value={index}
                checked={selectedAnswer === index}
                onChange={() => !answered && setSelectedAnswer(index)}
                style={styles.radioButton}
                disabled={answered}
              />
              <span style={styles.optionText}>{option}</span>
            </div>
          );
        })}
      </div>
      
      <div style={styles.actions}>
        {!showResult ? (
          <button 
            style={styles.submitButton}
            onClick={handleSubmit}
            disabled={selectedAnswer === null}
          >
            Submit Answer
          </button>
        ) : (
          <button 
            style={styles.retryButton}
            onClick={resetQuiz}
          >
            Try Again
          </button>
        )}
      </div>
      
      {showResult && (
        <div style={{
          ...styles.result,
          ...(selectedAnswer === correctAnswer ? styles.resultCorrect : styles.resultIncorrect)
        }}>
          <strong>
            {selectedAnswer === correctAnswer ? '✓ Correct!' : '✗ Incorrect'}
          </strong>
          <p style={{ marginTop: theme.spacing[2], marginBottom: 0 }}>
            {explanation}
          </p>
        </div>
      )}
    </div>
  );
};

// Drag and Drop component
export const TutorialDragDrop = ({
  items,
  categories,
  onComplete,
  instructions
}) => {
  const tutorial = useTutorial();
  const theme = useTheme();
  const [draggingItem, setDraggingItem] = useState(null);
  const [droppedItems, setDroppedItems] = useState({});
  const [feedback, setFeedback] = useState('');

  const handleDragStart = (e, item) => {
    setDraggingItem(item);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e, categoryId) => {
    e.preventDefault();
    if (!draggingItem) return;

    const newDroppedItems = { ...droppedItems };
    
    // Remove item from previous category
    Object.keys(newDroppedItems).forEach(cat => {
      newDroppedItems[cat] = newDroppedItems[cat].filter(item => item.id !== draggingItem.id);
    });
    
    // Add to new category
    if (!newDroppedItems[categoryId]) {
      newDroppedItems[categoryId] = [];
    }
    newDroppedItems[categoryId].push(draggingItem);
    
    setDroppedItems(newDroppedItems);
    setDraggingItem(null);
    
    // Check if completed
    if (items.every(item => 
      Object.values(newDroppedItems).some(category => 
        category.some(dropped => dropped.id === item.id)
      )
    )) {
      checkAnswers(newDroppedItems);
    }
  };

  const checkAnswers = (dropped) => {
    let correct = 0;
    let total = 0;
    
    items.forEach(item => {
      Object.entries(dropped).forEach(([categoryId, categoryItems]) => {
        const foundItem = categoryItems.find(ci => ci.id === item.id);
        if (foundItem) {
          total++;
          if (item.correctCategory === categoryId) {
            correct++;
          }
        }
      });
    });
    
    const percentage = Math.round((correct / total) * 100);
    setFeedback(`${correct} out of ${total} correct (${percentage}%)`);
    
    if (percentage >= 80) {
      onComplete && onComplete(true);
      tutorial.unlockAchievement('drag-drop-master');
    } else {
      onComplete && onComplete(false);
    }
  };

  const resetActivity = () => {
    setDroppedItems({});
    setFeedback('');
    setDraggingItem(null);
  };

  const styles = {
    container: {
      ...theme.cardStyle,
      margin: `${theme.spacing[6]} 0`
    },
    
    instructions: {
      fontSize: theme.typography.base,
      marginBottom: theme.spacing[6],
      color: theme.colors.textPrimary,
      lineHeight: 1.6
    },
    
    itemsContainer: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: theme.spacing[3],
      marginBottom: theme.spacing[6],
      padding: theme.spacing[4],
      border: `2px dashed ${theme.colors.border}`,
      borderRadius: theme.borderRadius.base,
      minHeight: 80
    },
    
    item: {
      padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
      backgroundColor: theme.colors.primary,
      color: '#ffffff',
      borderRadius: theme.borderRadius.base,
      cursor: 'grab',
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.medium,
      userSelect: 'none',
      transition: tutorial.reducedMotion ? 'none' : 'transform 0.2s ease'
    },
    
    itemDragging: {
      opacity: 0.5,
      transform: 'scale(1.05)'
    },
    
    categoriesContainer: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: theme.spacing[4],
      marginBottom: theme.spacing[4]
    },
    
    category: {
      border: `2px solid ${theme.colors.border}`,
      borderRadius: theme.borderRadius.base,
      padding: theme.spacing[4],
      minHeight: 120,
      transition: tutorial.reducedMotion ? 'none' : 'all 0.2s ease'
    },
    
    categoryDragOver: {
      borderColor: theme.colors.primary,
      backgroundColor: theme.colors.primaryLight + '10'
    },
    
    categoryTitle: {
      fontSize: theme.typography.base,
      fontWeight: theme.typography.semibold,
      marginBottom: theme.spacing[3],
      color: theme.colors.textPrimary
    },
    
    categoryItems: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: theme.spacing[2]
    },
    
    feedback: {
      padding: theme.spacing[3],
      borderRadius: theme.borderRadius.base,
      backgroundColor: theme.colors.gray100,
      color: theme.colors.textPrimary,
      marginBottom: theme.spacing[4],
      textAlign: 'center',
      fontWeight: theme.typography.medium
    },
    
    resetButton: {
      ...theme.buttonStyle,
      backgroundColor: theme.colors.accent
    }
  };

  const undroppedItems = items.filter(item => 
    !Object.values(droppedItems).some(category => 
      category.some(dropped => dropped.id === item.id)
    )
  );

  return (
    <div style={styles.container}>
      <p style={styles.instructions}>{instructions}</p>
      
      <div style={styles.itemsContainer}>
        {undroppedItems.map(item => (
          <div
            key={item.id}
            style={{
              ...styles.item,
              ...(draggingItem?.id === item.id ? styles.itemDragging : {})
            }}
            draggable
            onDragStart={(e) => handleDragStart(e, item)}
          >
            {item.label}
          </div>
        ))}
      </div>
      
      <div style={styles.categoriesContainer}>
        {categories.map(category => (
          <div
            key={category.id}
            style={styles.category}
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, category.id)}
          >
            <h4 style={styles.categoryTitle}>{category.name}</h4>
            <div style={styles.categoryItems}>
              {(droppedItems[category.id] || []).map(item => (
                <div key={item.id} style={styles.item}>
                  {item.label}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      {feedback && (
        <div style={styles.feedback}>
          {feedback}
        </div>
      )}
      
      <button style={styles.resetButton} onClick={resetActivity}>
        Reset Activity
      </button>
    </div>
  );
};

// Simulation component for interactive scenarios
export const TutorialSimulation = ({
  title,
  scenario,
  options,
  onDecision,
  currentState
}) => {
  const tutorial = useTutorial();
  const theme = useTheme();
  const [selectedOption, setSelectedOption] = useState(null);
  const [history, setHistory] = useState([]);

  const handleDecision = (option) => {
    setSelectedOption(option);
    const newHistory = [...history, { scenario, option, state: currentState }];
    setHistory(newHistory);
    onDecision && onDecision(option, newHistory);
  };

  const styles = {
    container: {
      ...theme.cardStyle,
      margin: `${theme.spacing[6]} 0`
    },
    
    title: {
      fontSize: theme.typography.xl,
      fontWeight: theme.typography.bold,
      marginBottom: theme.spacing[4],
      color: theme.colors.primary
    },
    
    scenario: {
      fontSize: theme.typography.base,
      lineHeight: 1.6,
      marginBottom: theme.spacing[6],
      padding: theme.spacing[4],
      backgroundColor: theme.colors.gray50,
      borderRadius: theme.borderRadius.base,
      borderLeft: `4px solid ${theme.colors.primary}`
    },
    
    options: {
      display: 'flex',
      flexDirection: 'column',
      gap: theme.spacing[3]
    },
    
    option: {
      padding: theme.spacing[4],
      border: `2px solid ${theme.colors.border}`,
      borderRadius: theme.borderRadius.base,
      cursor: 'pointer',
      transition: tutorial.reducedMotion ? 'none' : 'all 0.2s ease',
      backgroundColor: theme.colors.paper
    },
    
    optionHover: {
      borderColor: theme.colors.primary,
      backgroundColor: theme.colors.primaryLight + '10'
    },
    
    optionSelected: {
      borderColor: theme.colors.success,
      backgroundColor: theme.colors.successLight + '20'
    },
    
    history: {
      marginTop: theme.spacing[6],
      padding: theme.spacing[4],
      backgroundColor: theme.colors.gray50,
      borderRadius: theme.borderRadius.base
    },
    
    historyTitle: {
      fontSize: theme.typography.base,
      fontWeight: theme.typography.semibold,
      marginBottom: theme.spacing[3]
    },
    
    historyItem: {
      marginBottom: theme.spacing[2],
      fontSize: theme.typography.sm,
      color: theme.colors.textSecondary
    }
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>{title}</h3>
      
      <div style={styles.scenario}>
        {scenario}
      </div>
      
      <div style={styles.options}>
        {options.map((option, index) => (
          <div
            key={index}
            style={{
              ...styles.option,
              ...(selectedOption === option ? styles.optionSelected : {})
            }}
            onClick={() => handleDecision(option)}
          >
            <strong>{option.title}</strong>
            <p style={{ marginTop: theme.spacing[2], marginBottom: 0 }}>
              {option.description}
            </p>
          </div>
        ))}
      </div>
      
      {history.length > 0 && (
        <div style={styles.history}>
          <h4 style={styles.historyTitle}>Decision History</h4>
          {history.map((item, index) => (
            <div key={index} style={styles.historyItem}>
              Step {index + 1}: {item.option.title}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default {
  TutorialQuiz,
  TutorialDragDrop,
  TutorialSimulation
};