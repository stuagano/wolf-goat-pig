import React from "react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("[ErrorBoundary] Caught error:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      const isDev = process.env.NODE_ENV === "development";

      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "300px",
            padding: "40px 20px",
            textAlign: "center",
          }}
        >
          <div
            style={{
              background: "#1a1a2e",
              borderRadius: "12px",
              padding: "32px 40px",
              maxWidth: "480px",
              width: "100%",
              boxShadow: "0 4px 24px rgba(0,0,0,0.3)",
            }}
          >
            <div style={{ fontSize: "48px", marginBottom: "16px" }}>
              Something went wrong
            </div>
            <p
              style={{
                color: "#b0b0c0",
                fontSize: "16px",
                marginBottom: "24px",
                lineHeight: 1.5,
              }}
            >
              An unexpected error occurred. Please try again.
            </p>
            {isDev && this.state.error && (
              <pre
                style={{
                  background: "#12121e",
                  color: "#ff6b6b",
                  padding: "12px 16px",
                  borderRadius: "8px",
                  fontSize: "13px",
                  textAlign: "left",
                  overflow: "auto",
                  maxHeight: "160px",
                  marginBottom: "24px",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {this.state.error.toString()}
              </pre>
            )}
            <button
              onClick={this.handleReset}
              style={{
                background: "#4CAF50",
                color: "#fff",
                border: "none",
                borderRadius: "8px",
                padding: "12px 32px",
                fontSize: "16px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
