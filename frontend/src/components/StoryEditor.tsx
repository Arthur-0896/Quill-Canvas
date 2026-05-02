import React, { useState } from "react";

export default function StoryEditor() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [prompt, setPrompt] = useState<string>("");
  const [generationId, setGenerationId] = useState<string>("");

  const generateIllustration = async () => {
    if (!text.trim()) {
      setError("Please enter a story first");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setResult("");
      setPrompt("");
      setGenerationId("");

      console.log("Sending request to backend...");

      const res = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ story: text }),
      });

      console.log("Response status:", res.status);

      const data = await res.json();
      console.log("Response data:", data);

      // Check for errors in response
      if (!res.ok) {
        setError(data.detail || `Error: ${res.status} ${res.statusText}`);
        return;
      }

      if (data.error) {
        setError(data.error);
        return;
      }

      // Success - set all the data
      if (data.image_url) {
        setResult(data.image_url);
        setPrompt(data.prompt || "");
        setGenerationId(data.generation_id || "");
      } else {
        setError("No image URL returned from server");
      }
    } catch (err) {
      console.error("Request error:", err);
      setError(
        err instanceof Error
          ? `Network error: ${err.message}`
          : "Failed to connect to server. Make sure the backend is running on http://localhost:8000"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Allow Cmd/Ctrl + Enter to generate
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      generateIllustration();
    }
  };

  const generatePDF = async () => {
    if (!text.trim() || !result) {
      setError("Please generate an illustration first");
      return;
    }

    try {
      setPdfLoading(true);
      console.log("Generating PDF...");

      const res = await fetch("http://localhost:8000/generate-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          story: text,
          image_url: result,
          prompt: prompt,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || `Error generating PDF: ${res.status}`);
        return;
      }

      // Download the PDF
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `story_illustration_${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      console.log("PDF downloaded successfully");
    } catch (err) {
      console.error("PDF generation error:", err);
      setError(
        err instanceof Error
          ? `PDF error: ${err.message}`
          : "Failed to generate PDF"
      );
    } finally {
      setPdfLoading(false);
    }
  };

  const clearAll = () => {
    setText("");
    setResult("");
    setError("");
    setPrompt("");
    setGenerationId("");
  };

  return (
    <div style={styles.container}>
      {/* Left side - Story input */}
      <div style={styles.left}>
        <div style={styles.header}>
          <h1 style={styles.heading}>Your Story</h1>
          {text && (
            <button style={styles.clearButton} onClick={clearAll}>
              Clear
            </button>
          )}
        </div>

        <textarea
          style={styles.textarea}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Start writing your story here...&#10;&#10;Press Cmd/Ctrl + Enter to generate"
          disabled={loading}
        />

        <button
          style={{
            ...styles.button,
            ...(loading ? styles.buttonDisabled : {}),
          }}
          onClick={generateIllustration}
          disabled={loading || !text.trim()}
        >
          {loading ? "Generating..." : "Generate Illustration"}
        </button>

        {result && (
          <button
            style={{
              ...styles.pdfButton,
              ...(pdfLoading ? styles.buttonDisabled : {}),
            }}
            onClick={generatePDF}
            disabled={pdfLoading || !result}
          >
            {pdfLoading ? "Creating PDF..." : "📄 Export to PDF"}
          </button>
        )}

        {/* Show prompt if available */}
        {prompt && (
          <div style={styles.promptBox}>
            <strong>Generated Prompt:</strong>
            <div style={styles.promptText}>{prompt}</div>
          </div>
        )}

        {/* Show generation ID for debugging */}
        {generationId && (
          <div style={styles.debugInfo}>Generation ID: {generationId}</div>
        )}
      </div>

      {/* Right side - Image display */}
      <div style={styles.right}>
        {loading && (
          <div style={styles.loadingBox}>
            <div style={styles.spinner}></div>
            <div style={styles.loadingText}>
              Generating your illustration...
              <br />
              <span style={styles.loadingSubtext}>
                This may take 30-60 seconds
              </span>
            </div>
          </div>
        )}

        {error && !loading && (
          <div style={styles.errorBox}>
            <div style={styles.errorTitle}>⚠️ Error</div>
            <div style={styles.errorText}>{error}</div>
            <button style={styles.retryButton} onClick={generateIllustration}>
              Retry
            </button>
          </div>
        )}

        {result && !loading && !error && (
          <div style={styles.imageContainer}>
            <img
              src={result}
              alt="Generated illustration"
              style={styles.image}
              onError={() => setError("Failed to load image")}
            />
            <div style={styles.imageActions}>
              <a
                href={result}
                target="_blank"
                rel="noopener noreferrer"
                style={styles.link}
              >
                Open Full Size
              </a>
              <button
                style={styles.downloadButton}
                onClick={() => window.open(result, "_blank")}
              >
                Download
              </button>
            </div>
          </div>
        )}

        {!result && !loading && !error && (
          <div style={styles.imagePlaceholder}>
            <div style={styles.placeholderIcon}>🎨</div>
            <div style={styles.placeholderText}>
              Generated illustration will appear here
            </div>
            <div style={styles.placeholderSubtext}>
              Write your story and click "Generate Illustration"
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    display: "flex",
    height: "100vh",
    width: "100%",
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
  left: {
    flex: 1,
    padding: "40px",
    display: "flex",
    flexDirection: "column",
    backgroundColor: "#f9f9f9",
    gap: "16px",
    minWidth: "400px",
  },
  right: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#eaeaea",
    padding: "40px",
    minWidth: "400px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  heading: {
    fontSize: "32px",
    margin: 0,
    fontWeight: 600,
  },
  clearButton: {
    padding: "8px 16px",
    fontSize: "14px",
    backgroundColor: "transparent",
    color: "#666",
    border: "1px solid #ccc",
    borderRadius: "6px",
    cursor: "pointer",
    transition: "all 0.2s",
  },
  textarea: {
    flex: 1,
    width: "100%",
    padding: "20px",
    fontSize: "16px",
    lineHeight: 1.6,
    border: "1px solid #ddd",
    borderRadius: "8px",
    resize: "none",
    outline: "none",
    fontFamily: "inherit",
    transition: "border-color 0.2s",
  },
  button: {
    padding: "14px 24px",
    fontSize: "16px",
    fontWeight: 600,
    backgroundColor: "#111",
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    transition: "all 0.2s",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
  },
  buttonDisabled: {
    backgroundColor: "#999",
    cursor: "not-allowed",
  },
  pdfButton: {
    padding: "14px 24px",
    fontSize: "16px",
    fontWeight: 600,
    backgroundColor: "#0066cc",
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    transition: "all 0.2s",
    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
  },
  promptBox: {
    padding: "16px",
    backgroundColor: "#fff",
    border: "1px solid #ddd",
    borderRadius: "8px",
    fontSize: "14px",
    lineHeight: 1.5,
  },
  promptText: {
    marginTop: "8px",
    color: "#555",
    fontStyle: "italic",
  },
  debugInfo: {
    fontSize: "12px",
    color: "#999",
    fontFamily: "monospace",
  },
  loadingBox: {
    textAlign: "center",
  },
  spinner: {
    border: "4px solid #f3f3f3",
    borderTop: "4px solid #111",
    borderRadius: "50%",
    width: "50px",
    height: "50px",
    animation: "spin 1s linear infinite",
    margin: "0 auto 20px",
  },
  loadingText: {
    fontSize: "18px",
    color: "#333",
    fontWeight: 500,
  },
  loadingSubtext: {
    fontSize: "14px",
    color: "#666",
    fontWeight: 400,
    marginTop: "8px",
    display: "block",
  },
  errorBox: {
    maxWidth: "500px",
    padding: "30px",
    backgroundColor: "#fff",
    border: "2px solid #ff4444",
    borderRadius: "12px",
    textAlign: "center",
  },
  errorTitle: {
    fontSize: "24px",
    fontWeight: 600,
    color: "#ff4444",
    marginBottom: "16px",
  },
  errorText: {
    fontSize: "16px",
    color: "#666",
    marginBottom: "20px",
    lineHeight: 1.5,
    whiteSpace: "pre-wrap",
  },
  retryButton: {
    padding: "12px 24px",
    fontSize: "16px",
    backgroundColor: "#111",
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: 600,
  },
  imagePlaceholder: {
    width: "80%",
    maxWidth: "500px",
    height: "60%",
    border: "2px dashed #999",
    borderRadius: "12px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    color: "#666",
    textAlign: "center",
    padding: "40px",
  },
  placeholderIcon: {
    fontSize: "64px",
    marginBottom: "20px",
  },
  placeholderText: {
    fontSize: "18px",
    fontWeight: 500,
    marginBottom: "8px",
  },
  placeholderSubtext: {
    fontSize: "14px",
    color: "#999",
  },
  imageContainer: {
    width: "100%",
    height: "100%",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  image: {
    width: "100%",
    height: "calc(100% - 60px)",
    objectFit: "contain",
    backgroundColor: "white",
    borderRadius: "12px",
    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
  },
  imageActions: {
    display: "flex",
    gap: "12px",
    justifyContent: "center",
  },
  link: {
    padding: "10px 20px",
    fontSize: "14px",
    color: "#111",
    textDecoration: "none",
    border: "1px solid #111",
    borderRadius: "6px",
    transition: "all 0.2s",
  },
  downloadButton: {
    padding: "10px 20px",
    fontSize: "14px",
    backgroundColor: "#111",
    color: "white",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: 600,
  },
};

// Add keyframe animation for spinner
const styleSheet = document.createElement("style");
styleSheet.textContent = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;
document.head.appendChild(styleSheet);