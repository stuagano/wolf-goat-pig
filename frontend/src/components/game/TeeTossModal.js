import React, { useState, useEffect } from 'react';

const COLORS = {
    primary: "#1976d2",
    accent: "#00bcd4",
    success: "#388e3c",
    bg: "#f9fafe",
    card: "#fff",
    text: "#222",
    border: "#e0e0e0",
};

const modalOverlayStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.7)',
    zIndex: 1100,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
};

const modalContentStyle = {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    width: '90%',
    maxWidth: 600,
    maxHeight: '90vh',
    padding: 24,
    boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
    display: 'flex',
    flexDirection: 'column',
    overflowY: 'auto',
};

const buttonStyle = {
    background: COLORS.primary,
    color: "#fff",
    border: "none",
    borderRadius: 8,
    padding: "10px 20px",
    fontWeight: 600,
    fontSize: 16,
    cursor: "pointer",
    transition: "background 0.2s",
    margin: '0 8px',
};

const TeeIcon = ({ rotation }) => (
    <svg
        width="100"
        height="100"
        viewBox="0 0 100 100"
        style={{
            transform: `rotate(${rotation}deg)`,
            transition: 'transform 3s cubic-bezier(0.25, 0.1, 0.25, 1)',
            filter: 'drop-shadow(2px 4px 6px rgba(0,0,0,0.3))'
        }}
    >
        {/* Simple Golf Tee Shape - Pointing UP */}
        <path d="M45,90 L55,90 L55,70 L52,15 L48,15 L45,70 Z" fill="#ff9800" stroke="#e65100" strokeWidth="1" />
        <ellipse cx="50" cy="90" rx="12" ry="4" fill="#ffd180" stroke="#e65100" strokeWidth="1" />
    </svg>
);

const PlayerCircle = ({ players, rotation, onSpinComplete, isSpinning }) => {
    const radius = 120;
    const center = 150;

    return (
        <div style={{ position: 'relative', width: 300, height: 300, margin: '0 auto' }}>
            {/* Players arranged in a circle */}
            {players.map((player, index) => {
                const angle = (index * (360 / players.length)) - 90; // Start at top
                const radian = (angle * Math.PI) / 180;
                const x = center + radius * Math.cos(radian);
                const y = center + radius * Math.sin(radian);

                return (
                    <div
                        key={player.id}
                        style={{
                            position: 'absolute',
                            left: x,
                            top: y,
                            transform: 'translate(-50%, -50%)',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            width: 80,
                            textAlign: 'center',
                        }}
                    >
                        <div style={{
                            width: 40,
                            height: 40,
                            borderRadius: '50%',
                            background: COLORS.accent,
                            color: 'white',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 'bold',
                            marginBottom: 4,
                            boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                        }}>
                            {player.name.charAt(0)}
                        </div>
                        <span style={{ fontSize: 12, fontWeight: 600, background: 'rgba(255,255,255,0.8)', padding: '2px 4px', borderRadius: 4 }}>
                            {player.name}
                        </span>
                    </div>
                );
            })}

            {/* Center Tee */}
            <div style={{
                position: 'absolute',
                left: '50%',
                top: '50%',
                transform: 'translate(-50%, -50%)',
                zIndex: 10
            }}>
                <TeeIcon rotation={rotation} />
            </div>
        </div>
    );
};

const TeeTossModal = ({ players, onClose, onOrderComplete }) => {
    const [mode, setMode] = useState('animate'); // 'animate' or 'manual'
    const [orderedPlayers, setOrderedPlayers] = useState([]);
    const [remainingPlayers, setRemainingPlayers] = useState([...players]);
    const [rotation, setRotation] = useState(0);
    const [isSpinning, setIsSpinning] = useState(false);
    const [message, setMessage] = useState("Tap 'Spin' to toss the tee!");

    // For manual mode
    const [manualOrder, setManualOrder] = useState([...players]);

    const spinTee = () => {
        if (isSpinning || remainingPlayers.length === 0) return;

        setIsSpinning(true);
        setMessage("Spinning...");

        // Calculate random rotation (at least 3 full spins + random angle)
        const randomAngle = Math.floor(Math.random() * 360);
        const totalRotation = rotation + 1080 + randomAngle;

        setRotation(totalRotation);

        // Determine winner based on angle
        // The tee points UP at 0 degrees. 
        // Players are arranged starting at -90 (top) which corresponds to 0 degrees for the tee if we align them.
        // Let's simplify: The tee graphic points UP. 
        // At 0 deg rotation, it points to 12 o'clock.
        // Player 0 is at 12 o'clock (-90 deg in circle math, but let's map rotation to player index).

        // Normalize final angle to 0-360
        const finalAngle = totalRotation % 360;

        // Each player occupies a segment
        const segmentSize = 360 / remainingPlayers.length;

        // Calculate index. 
        // Note: SVG rotation is clockwise. 0 is up.
        // Player 0 is at 0 deg (up). Player 1 is at segmentSize deg (right-ish).
        // We need to find which segment the pointer lands in.
        // We need to account for the "pointer" of the tee. 
        // Assuming the tee points UP at 0 rotation.

        // Let's wait for animation to finish to update state
        setTimeout(() => {
            // Determine selected player index
            // We add offset because the first player is centered at 0 (up)
            // So the segment for player 0 is from -segmentSize/2 to +segmentSize/2
            // But we are working with 0-360 positive.
            // Let's shift angle by half segment to align boundaries.
            // If angle > 360 - halfSegment, it belongs to player 0
            // Or if angle < halfSegment, it belongs to player 0

            const halfSegment = segmentSize / 2;
            let selectedIndex = Math.floor(((finalAngle + halfSegment) % 360) / segmentSize);

            const winner = remainingPlayers[selectedIndex];

            setOrderedPlayers(prev => [...prev, winner]);
            setRemainingPlayers(prev => prev.filter(p => p.id !== winner.id));
            setIsSpinning(false);
            setMessage(`${winner.name} is #${orderedPlayers.length + 1}!`);

            // Reset rotation visually (optional, but keeps numbers smaller)
            // setRotation(finalAngle); 

        }, 3000); // Match CSS transition time
    };

    // Auto-complete if only 1 player left
    useEffect(() => {
        if (remainingPlayers.length === 1 && !isSpinning && orderedPlayers.length > 0) {
            const lastPlayer = remainingPlayers[0];
            setOrderedPlayers(prev => [...prev, lastPlayer]);
            setRemainingPlayers([]);
            setMessage("Order determined!");
        }
    }, [remainingPlayers, isSpinning, orderedPlayers]);

    const handleManualDragStart = (e, index) => {
        e.dataTransfer.setData("index", index);
    };

    const handleManualDrop = (e, dropIndex) => {
        const dragIndex = parseInt(e.dataTransfer.getData("index"));
        if (dragIndex === dropIndex) return;

        const newOrder = [...manualOrder];
        const [removed] = newOrder.splice(dragIndex, 1);
        newOrder.splice(dropIndex, 0, removed);
        setManualOrder(newOrder);
    };

    const handleConfirm = () => {
        if (mode === 'animate') {
            onOrderComplete(orderedPlayers);
        } else {
            onOrderComplete(manualOrder);
        }
    };

    return (
        <div style={modalOverlayStyle}>
            <div style={modalContentStyle}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                    <h2 style={{ margin: 0, color: COLORS.primary }}>Toss Tees for Order</h2>
                    <button onClick={onClose} style={{ background: 'transparent', border: 'none', fontSize: 24, cursor: 'pointer' }}>×</button>
                </div>

                {/* Mode Toggle */}
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 20, background: '#eee', padding: 4, borderRadius: 8 }}>
                    <button
                        onClick={() => setMode('animate')}
                        style={{
                            flex: 1,
                            border: 'none',
                            background: mode === 'animate' ? 'white' : 'transparent',
                            padding: 8,
                            borderRadius: 6,
                            fontWeight: 600,
                            boxShadow: mode === 'animate' ? '0 2px 4px rgba(0,0,0,0.1)' : 'none',
                            cursor: 'pointer'
                        }}
                    >
                        Interactive Toss
                    </button>
                    <button
                        onClick={() => setMode('manual')}
                        style={{
                            flex: 1,
                            border: 'none',
                            background: mode === 'manual' ? 'white' : 'transparent',
                            padding: 8,
                            borderRadius: 6,
                            fontWeight: 600,
                            boxShadow: mode === 'manual' ? '0 2px 4px rgba(0,0,0,0.1)' : 'none',
                            cursor: 'pointer'
                        }}
                    >
                        Manual List
                    </button>
                </div>

                {mode === 'animate' ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <div style={{ marginBottom: 10, fontSize: 18, fontWeight: 600, color: COLORS.primary }}>
                            {message}
                        </div>

                        {remainingPlayers.length > 0 ? (
                            <PlayerCircle
                                players={remainingPlayers}
                                rotation={rotation}
                                isSpinning={isSpinning}
                            />
                        ) : (
                            <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                                <div style={{ fontSize: 48, marginBottom: 20 }}>🎉</div>
                                <h3>All Set!</h3>
                            </div>
                        )}

                        <div style={{ marginTop: 20, width: '100%' }}>
                            <h4 style={{ borderBottom: '1px solid #eee', paddingBottom: 8 }}>Current Order:</h4>
                            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                                {orderedPlayers.map((p, i) => (
                                    <div key={p.id} style={{
                                        background: '#f0f0f0',
                                        padding: '8px 16px',
                                        borderRadius: 20,
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: 8
                                    }}>
                                        <span style={{
                                            background: COLORS.primary,
                                            color: 'white',
                                            width: 20,
                                            height: 20,
                                            borderRadius: '50%',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontSize: 12
                                        }}>{i + 1}</span>
                                        {p.name}
                                    </div>
                                ))}
                                {remainingPlayers.length > 0 && (
                                    <div style={{ color: '#999', padding: '8px 0', fontStyle: 'italic' }}>
                                        ... {remainingPlayers.length} more to go
                                    </div>
                                )}
                            </div>
                        </div>

                        <div style={{ marginTop: 30, display: 'flex', gap: 10 }}>
                            {remainingPlayers.length > 0 && (
                                <button
                                    onClick={spinTee}
                                    disabled={isSpinning}
                                    style={{ ...buttonStyle, background: isSpinning ? '#ccc' : COLORS.accent, fontSize: 20, padding: '12px 32px' }}
                                >
                                    {isSpinning ? 'Spinning...' : 'Spin Tee'}
                                </button>
                            )}
                            {remainingPlayers.length === 0 && (
                                <button onClick={handleConfirm} style={{ ...buttonStyle, background: COLORS.success }}>
                                    Use This Order
                                </button>
                            )}
                        </div>
                    </div>
                ) : (
                    <div>
                        <p style={{ color: '#666', marginBottom: 16 }}>Drag and drop to reorder players.</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {manualOrder.map((player, index) => (
                                <div
                                    key={player.id}
                                    draggable
                                    onDragStart={(e) => handleManualDragStart(e, index)}
                                    onDragOver={(e) => e.preventDefault()}
                                    onDrop={(e) => handleManualDrop(e, index)}
                                    style={{
                                        padding: 16,
                                        background: '#f8f9fa',
                                        border: '1px solid #dee2e6',
                                        borderRadius: 8,
                                        display: 'flex',
                                        alignItems: 'center',
                                        cursor: 'grab',
                                        transition: 'background 0.2s'
                                    }}
                                >
                                    <span style={{
                                        fontSize: 20,
                                        fontWeight: 'bold',
                                        color: COLORS.primary,
                                        width: 40
                                    }}>{index + 1}.</span>
                                    <span style={{ fontSize: 18, flex: 1 }}>{player.name}</span>
                                    <span style={{ color: '#999' }}>☰</span>
                                </div>
                            ))}
                        </div>
                        <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end' }}>
                            <button onClick={handleConfirm} style={{ ...buttonStyle, background: COLORS.success }}>
                                Confirm Order
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TeeTossModal;
