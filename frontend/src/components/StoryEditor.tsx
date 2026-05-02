import React, { useState } from "react";

export default function StoryEditor() {
  const [text, setText] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  const generateIllustration = async () => {
    if (!text.trim()) return;

    try {
      setLoading(true);

      const res = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ story: text }),
      });

      const data = await res.json();
      setResult(data.output);
    } catch (err) {
      setResult("Error generating response");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Left side */}
      <div style={styles.left}>
        <h1 style={styles.heading}>Your Story</h1>

        <textarea
          style={styles.textarea}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Start writing your story here..."
        />

        <button style={styles.button} onClick={generateIllustration}>
          {loading ? "Generating..." : "Generate Illustration"}
        </button>
      </div>

      {/* Right side */}
      <div style={styles.right}>
        {result ? (
          <div style={styles.resultBox}>{result}</div>
        ) : (
          <div style={styles.imagePlaceholder}>
            Generated output will appear here
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
    fontFamily: "Arial, sans-serif",
  },
  left: {
    flex: 1,
    padding: "40px",
    display: "flex",
    flexDirection: "column",
    backgroundColor: "#f9f9f9",
    gap: "12px",
  },
  right: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#eaeaea",
    padding: "40px",
  },
  heading: {
    fontSize: "32px",
    marginBottom: "10px",
  },
  textarea: {
    flex: 1,
    width: "100%",
    padding: "20px",
    fontSize: "18px",
    lineHeight: 1.6,
    border: "1px solid #ccc",
    borderRadius: "8px",
    resize: "none",
    outline: "none",
  },
  button: {
    padding: "12px",
    fontSize: "16px",
    backgroundColor: "#111",
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
  },
  imagePlaceholder: {
    width: "80%",
    height: "60%",
    border: "2px dashed #999",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#666",
    fontSize: "18px",
    textAlign: "center",
  },
  resultBox: {
    width: "100%",
    height: "100%",
    backgroundColor: "white",
    padding: "20px",
    borderRadius: "8px",
    overflowY: "auto",
    whiteSpace: "pre-wrap",
    fontSize: "16px",
  },
};