import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="container" style={{ textAlign: "center", padding: "100px 20px" }}>
          <h2 style={{ fontSize: "24px", color: "#ef4444", marginBottom: "12px" }}>
            Something went wrong loading this title
          </h2>
          <p style={{ color: "#94a3b8", marginBottom: "24px" }}>
            {this.state.error?.message || "An unexpected error occurred while rendering the page."}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary"
            style={{ marginRight: "12px" }}
          >
            🔄 Refresh Page
          </button>
          <a href="/" className="btn-secondary" style={{ textDecoration: "none" }}>
            Back to Home
          </a>
        </div>
      );
    }

    return this.props.children;
  }
}
