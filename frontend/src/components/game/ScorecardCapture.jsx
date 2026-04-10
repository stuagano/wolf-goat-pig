import React, { useRef, useState, useEffect } from 'react';

/**
 * ScorecardCapture — camera input with preview and retake flow.
 * Uses <input type="file" capture="environment"> for mobile camera access.
 */
const ScorecardCapture = ({ onCapture, onCancel, onManualEntry }) => {
  const inputRef = useRef(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [capturedFile, setCapturedFile] = useState(null);

  // Clean up object URL on unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setCapturedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleRetake = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setCapturedFile(null);
    // Reset the input so the same file can be re-selected
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleUse = () => {
    if (capturedFile) onCapture(capturedFile);
  };

  return (
    <div className="flex flex-col items-center gap-4 p-4">
      <h2 className="text-xl font-bold text-gray-900">Scan Scorecard</h2>
      <p className="text-sm text-gray-500 text-center">
        Make sure all 18 holes and player quarter totals are visible.
      </p>

      {!previewUrl ? (
        <div className="flex flex-col items-center gap-3 w-full">
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleFileChange}
            className="hidden"
            id="scorecard-camera-input"
          />
          <label
            htmlFor="scorecard-camera-input"
            className="w-full py-4 bg-blue-600 text-white text-center rounded-xl font-semibold text-lg cursor-pointer hover:bg-blue-700 transition-colors"
          >
            📷 Take Photo
          </label>
          <label
            htmlFor="scorecard-camera-input"
            className="w-full py-3 bg-gray-100 text-gray-700 text-center rounded-xl font-medium cursor-pointer hover:bg-gray-200 transition-colors"
            onClick={() => {
              // Remove capture attribute to allow gallery selection
              if (inputRef.current) inputRef.current.removeAttribute('capture');
            }}
          >
            🖼 Choose from Library
          </label>
          {onManualEntry && (
            <button
              onClick={onManualEntry}
              className="text-sm text-blue-500 hover:text-blue-700 mt-1"
            >
              ✏️ Enter manually instead
            </button>
          )}
          <button
            onClick={onCancel}
            className="text-sm text-gray-400 hover:text-gray-600 mt-1"
          >
            Cancel
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-4 w-full">
          <img
            src={previewUrl}
            alt="Scorecard preview"
            className="w-full max-h-80 object-contain rounded-xl border border-gray-200"
          />
          <div className="flex gap-3 w-full">
            <button
              onClick={handleRetake}
              className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-300 transition-colors"
            >
              Retake
            </button>
            <button
              onClick={handleUse}
              className="flex-1 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors"
            >
              Use Photo →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScorecardCapture;
