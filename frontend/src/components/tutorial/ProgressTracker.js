import React, { useState, useEffect } from 'react';
import { useTutorial } from '../../context/TutorialContext';
import { useTutorialProgress } from '../../hooks/useTutorialProgress';
import { useTheme } from '../../theme/Provider';

const ProgressTracker = () => {
  const tutorial = useTutorial();
  const progress = useTutorialProgress();
  const theme = useTheme();
  const [expandedModule, setExpandedModule] = useState(tutorial.currentModule);
  const [showAchievements, setShowAchievements] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);

  // Auto-expand current module
  useEffect(() => {
    setExpandedModule(tutorial.currentModule);
  }, [tutorial.currentModule]);

  const formatTime = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getModuleIcon = (moduleId) => {
    const icons = {
      'golf-basics': '⛳',
      'game-overview': '🎯',
      'team-formation': '👥',
      'betting-system': '💰',
      'advanced-rules': '📜',
      'analysis-tools': '📊',
      'practice-game': '🎮'
    };
    return icons[moduleId] || '📖';
  };

  const getAchievementIcon = (achievementId) => {
    const icons = {
      'first-steps': '👶',
      'speed-learner': '⚡',
      'quarter-complete': '🥉',
      'halfway-hero': '🥈',
      'almost-expert': '🥇',
      'wgp-master': '👑',
      'quiz-ace': '🧠',
      'completionist': '💯'
    };
    return icons[achievementId] || '🏆';
  };

  const getAchievementTitle = (achievementId) => {
    const titles = {
      'first-steps': 'First Steps',
      'speed-learner': 'Speed Learner',
      'quarter-complete': 'Quarter Complete',
      'halfway-hero': 'Halfway Hero',
      'almost-expert': 'Almost Expert',
      'wgp-master': 'WGP Master',
      'quiz-ace': 'Quiz Ace',
      'completionist': 'Completionist'
    };
    return titles[achievementId] || achievementId;
  };

  const analytics = progress.getAnalytics();
  const recommendations = progress.getRecommendations();

  const styles = {
    container: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    },
    
    overallProgress: {
      padding: theme.spacing[4],
      borderBottom: `1px solid ${theme.colors.border}`
    },
    
    progressTitle: {
      fontSize: theme.typography.base,
      fontWeight: theme.typography.semibold,
      marginBottom: theme.spacing[3],
      color: theme.colors.textPrimary
    },
    
    progressBar: {
      width: '100%',
      height: 12,
      backgroundColor: theme.colors.gray200,
      borderRadius: theme.borderRadius.full,
      overflow: 'hidden',
      marginBottom: theme.spacing[2]
    },
    
    progressFill: {
      height: '100%',
      backgroundColor: tutorial.overallProgress === 100 ? theme.colors.success : theme.colors.primary,
      transition: tutorial.reducedMotion ? 'none' : 'width 0.5s ease',
      borderRadius: theme.borderRadius.full
    },
    
    progressText: {
      fontSize: theme.typography.sm,
      color: theme.colors.textSecondary,
      textAlign: 'center'
    },
    
    moduleList: {
      flex: 1,
      overflow: 'auto',
      padding: theme.spacing[2]
    },
    
    moduleItem: {
      marginBottom: theme.spacing[2]
    },
    
    moduleHeader: {
      display: 'flex',
      alignItems: 'center',
      padding: theme.spacing[3],
      background: theme.colors.gray50,
      borderRadius: theme.borderRadius.base,
      cursor: 'pointer',
      border: `1px solid ${theme.colors.border}`,
      transition: tutorial.reducedMotion ? 'none' : 'all 0.2s ease'
    },
    
    moduleHeaderActive: {
      background: theme.colors.primary,
      color: '#ffffff',
      borderColor: theme.colors.primary
    },
    
    moduleHeaderCompleted: {
      background: theme.colors.success,
      color: '#ffffff',
      borderColor: theme.colors.success
    },
    
    moduleIcon: {
      fontSize: '1.2rem',
      marginRight: theme.spacing[3],
      minWidth: '1.5rem'
    },
    
    moduleInfo: {
      flex: 1,
      minWidth: 0
    },
    
    moduleTitle: {
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.medium,
      marginBottom: theme.spacing[1],
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap'
    },
    
    moduleProgress: {
      fontSize: theme.typography.xs,
      opacity: 0.8
    },
    
    moduleExpanded: {
      padding: theme.spacing[3],
      background: theme.colors.paper,
      border: `1px solid ${theme.colors.border}`,
      borderTop: 'none',
      borderRadius: `0 0 ${theme.borderRadius.base} ${theme.borderRadius.base}`
    },
    
    moduleDetails: {
      fontSize: theme.typography.sm,
      lineHeight: 1.4,
      marginBottom: theme.spacing[3]
    },
    
    moduleStats: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: theme.spacing[2],
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary
    },
    
    statItem: {
      display: 'flex',
      justifyContent: 'space-between'
    },
    
    tabContainer: {
      borderTop: `1px solid ${theme.colors.border}`,
      background: theme.colors.gray50
    },
    
    tabButtons: {
      display: 'flex',
      borderBottom: `1px solid ${theme.colors.border}`
    },
    
    tabButton: {
      flex: 1,
      padding: theme.spacing[3],
      background: 'transparent',
      border: 'none',
      fontSize: theme.typography.sm,
      cursor: 'pointer',
      borderBottom: '2px solid transparent',
      transition: tutorial.reducedMotion ? 'none' : 'all 0.2s ease'
    },
    
    tabButtonActive: {
      borderBottomColor: theme.colors.primary,
      color: theme.colors.primary,
      fontWeight: theme.typography.semibold
    },
    
    tabContent: {
      padding: theme.spacing[4],
      maxHeight: 200,
      overflow: 'auto'
    },
    
    achievementGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
      gap: theme.spacing[2]
    },
    
    achievement: {
      textAlign: 'center',
      padding: theme.spacing[2],
      borderRadius: theme.borderRadius.base,
      background: theme.colors.gray100,
      fontSize: theme.typography.xs
    },
    
    achievementUnlocked: {
      background: theme.colors.success,
      color: '#ffffff'
    },
    
    achievementIcon: {
      fontSize: '1.5rem',
      marginBottom: theme.spacing[1]
    },
    
    analyticsGrid: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: theme.spacing[3],
      fontSize: theme.typography.sm
    },
    
    analyticsItem: {
      textAlign: 'center'
    },
    
    analyticsValue: {
      fontSize: theme.typography.lg,
      fontWeight: theme.typography.bold,
      color: theme.colors.primary,
      marginBottom: theme.spacing[1]
    },
    
    analyticsLabel: {
      color: theme.colors.textSecondary,
      fontSize: theme.typography.xs
    },
    
    recommendations: {
      marginTop: theme.spacing[4]
    },
    
    recommendation: {
      padding: theme.spacing[3],
      borderRadius: theme.borderRadius.base,
      marginBottom: theme.spacing[2],
      fontSize: theme.typography.sm,
      lineHeight: 1.4
    },
    
    recommendationHigh: {
      background: theme.colors.errorLight,
      color: theme.colors.errorDark,
      border: `1px solid ${theme.colors.error}`
    },
    
    recommendationMedium: {
      background: theme.colors.warningLight,
      color: theme.colors.warningDark,
      border: `1px solid ${theme.colors.warning}`
    },
    
    recommendationLow: {
      background: theme.colors.gray100,
      color: theme.colors.textPrimary,
      border: `1px solid ${theme.colors.border}`
    }
  };

  const handleModuleClick = (moduleId) => {
    if (tutorial.canAdvanceToModule(moduleId)) {
      tutorial.goToModule(moduleId);
    }
    setExpandedModule(expandedModule === moduleId ? null : moduleId);
  };

  const achievements = [
    'first-steps', 'speed-learner', 'quarter-complete', 'halfway-hero',
    'almost-expert', 'wgp-master', 'quiz-ace', 'completionist'
  ];

  return (
    <div style={styles.container}>
      {/* Overall progress */}
      <div style={styles.overallProgress}>
        <div style={styles.progressTitle}>Overall Progress</div>
        <div style={styles.progressBar}>
          <div 
            style={{
              ...styles.progressFill,
              width: `${tutorial.overallProgress}%`
            }}
          />
        </div>
        <div style={styles.progressText}>
          {tutorial.overallProgress}% Complete
        </div>
      </div>

      {/* Module list */}
      <div style={styles.moduleList}>
        {tutorial.modules.map((module) => {
          const isActive = module.id === tutorial.currentModule;
          const isCompleted = tutorial.completedModules.has(module.id);
          const canAccess = tutorial.canAdvanceToModule(module.id);
          const moduleProgress = tutorial.getModuleProgress(module.id);
          const timeSpent = tutorial.timeSpent[module.id] || 0;
          
          let headerStyle = styles.moduleHeader;
          if (isCompleted) headerStyle = { ...headerStyle, ...styles.moduleHeaderCompleted };
          else if (isActive) headerStyle = { ...headerStyle, ...styles.moduleHeaderActive };
          
          return (
            <div key={module.id} style={styles.moduleItem}>
              <div 
                style={{
                  ...headerStyle,
                  opacity: canAccess ? 1 : 0.6,
                  cursor: canAccess ? 'pointer' : 'not-allowed'
                }}
                onClick={() => canAccess && handleModuleClick(module.id)}
              >
                <div style={styles.moduleIcon}>
                  {getModuleIcon(module.id)}
                </div>
                
                <div style={styles.moduleInfo}>
                  <div style={styles.moduleTitle}>{module.title}</div>
                  <div style={styles.moduleProgress}>
                    {isCompleted ? 'Completed' : `${moduleProgress}%`}
                    {timeSpent > 0 && ` • ${formatTime(timeSpent)}`}
                  </div>
                </div>
                
                {isCompleted && <span>✓</span>}
              </div>
              
              {expandedModule === module.id && (
                <div style={styles.moduleExpanded}>
                  <div style={styles.moduleDetails}>
                    {module.description}
                  </div>
                  
                  <div style={styles.moduleStats}>
                    <div style={styles.statItem}>
                      <span>Duration:</span>
                      <span>{module.duration} min</span>
                    </div>
                    <div style={styles.statItem}>
                      <span>Progress:</span>
                      <span>{moduleProgress}%</span>
                    </div>
                    <div style={styles.statItem}>
                      <span>Time spent:</span>
                      <span>{formatTime(timeSpent)}</span>
                    </div>
                    <div style={styles.statItem}>
                      <span>Required:</span>
                      <span>{module.requiredForNext ? 'Yes' : 'No'}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Bottom tabs */}
      <div style={styles.tabContainer}>
        <div style={styles.tabButtons}>
          <button 
            style={{
              ...styles.tabButton,
              ...(showAchievements ? styles.tabButtonActive : {})
            }}
            onClick={() => {
              setShowAchievements(!showAchievements);
              setShowAnalytics(false);
            }}
          >
            🏆 Achievements
          </button>
          <button 
            style={{
              ...styles.tabButton,
              ...(showAnalytics ? styles.tabButtonActive : {})
            }}
            onClick={() => {
              setShowAnalytics(!showAnalytics);
              setShowAchievements(false);
            }}
          >
            📊 Analytics
          </button>
        </div>
        
        {showAchievements && (
          <div style={styles.tabContent}>
            <div style={styles.achievementGrid}>
              {achievements.map(achievementId => {
                const isUnlocked = tutorial.achievements.has(achievementId);
                return (
                  <div 
                    key={achievementId}
                    style={{
                      ...styles.achievement,
                      ...(isUnlocked ? styles.achievementUnlocked : {})
                    }}
                  >
                    <div style={styles.achievementIcon}>
                      {getAchievementIcon(achievementId)}
                    </div>
                    <div>{getAchievementTitle(achievementId)}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
        
        {showAnalytics && (
          <div style={styles.tabContent}>
            <div style={styles.analyticsGrid}>
              <div style={styles.analyticsItem}>
                <div style={styles.analyticsValue}>
                  {formatTime(analytics.sessionTime)}
                </div>
                <div style={styles.analyticsLabel}>Session Time</div>
              </div>
              
              <div style={styles.analyticsItem}>
                <div style={styles.analyticsValue}>
                  {Math.round(analytics.quizAccuracy * 100)}%
                </div>
                <div style={styles.analyticsLabel}>Quiz Accuracy</div>
              </div>
              
              <div style={styles.analyticsItem}>
                <div style={styles.analyticsValue}>
                  {Math.round(analytics.learningEfficiency)}%
                </div>
                <div style={styles.analyticsLabel}>Efficiency</div>
              </div>
              
              <div style={styles.analyticsItem}>
                <div style={styles.analyticsValue}>
                  {analytics.achievementCount}
                </div>
                <div style={styles.analyticsLabel}>Achievements</div>
              </div>
            </div>
            
            {recommendations.length > 0 && (
              <div style={styles.recommendations}>
                <div style={{...styles.progressTitle, marginBottom: theme.spacing[2]}}>
                  Recommendations
                </div>
                {recommendations.map((rec, index) => {
                  let recStyle = styles.recommendation;
                  if (rec.priority === 'high') recStyle = {...recStyle, ...styles.recommendationHigh};
                  else if (rec.priority === 'medium') recStyle = {...recStyle, ...styles.recommendationMedium};
                  else recStyle = {...recStyle, ...styles.recommendationLow};
                  
                  return (
                    <div key={index} style={recStyle}>
                      {rec.message}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressTracker;