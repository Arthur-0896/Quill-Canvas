import React, { useEffect, useState } from "react";

export default function StoryEditor() {
  const [text, setText] = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [hasTriggered, setHasTriggered] = useState(false);

  // word counter
  const getWordCount = (str: string) =>
    str.trim().split(/\s+/).filter(Boolean).length;

  const wordCount = getWordCount(text);

  // auto trigger at 300 words
  useEffect(() => {
    if (wordCount >= 300 && !hasTriggered) {
      setHasTriggered(true);
      sendToBackend();
    }
  }, [wordCount]);

  const sendToBackend = async () => {
    setLoading(true);
    setOutput("");

    try {
      const res = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ story: text }),
      });

      const data = await res.json();

      console.log("🔵 Backend response:", data);

      // robust parsing (handles all backend shapes)
      const result =
        data.output?.content ||
        data.output?.text ||
        data.output ||
        JSON.stringify(data, null, 2);

      setOutput(result);
    } catch (err) {
      console.error("🔴 Fetch error:", err);
      setOutput("Error connecting to backend");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setHasTriggered(false);
    setOutput("");
    setText("");
  };

  return (
    <div style={styles.container}>
      {/* LEFT */}
      <div style={styles.left}>
        <h2>Story Editor</h2>

        <textarea
          style={styles.textarea}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Start writing your story..."
        />

        <div style={styles.footer}>
          <p>Words: {wordCount} / 300</p>

          <button onClick={sendToBackend} style={styles.button}>
            Generate Now
          </button>

          <button onClick={handleReset} style={styles.buttonSecondary}>
            Reset
          </button>
        </div>
      </div>

      {/* RIGHT */}
      <div style={styles.right}>
        {loading ? (
          <p>Generating image prompt...</p>
        ) : output ? (
          <pre style={styles.output}>{output}</pre>
        ) : (
          <p>Output will appear here</p>
        )}
      </div>
    </div>
  );
}

const styles: any = {
  container: {
    display: "flex",
    height: "100vh",
    fontFamily: "Arial",
  },
  left: {
    flex: 1,
    padding: 20,
    display: "flex",
    flexDirection: "column",
  },
  right: {
    flex: 1,
    padding: 20,
    backgroundColor: "#f4f4f4",
    overflowY: "auto",
  },
  textarea: {
    flex: 1,
    fontSize: 16,
    padding: 12,
    borderRadius: 8,
    border: "1px solid #ccc",
    resize: "none",
  },
  footer: {
    marginTop: 10,
  },
  button: {
    marginRight: 10,
    padding: "8px 12px",
    background: "black",
    color: "white",
    border: "none",
    cursor: "pointer",
  },
  buttonSecondary: {
    padding: "8px 12px",
    background: "#ddd",
    border: "none",
    cursor: "pointer",
  },
  output: {
    whiteSpace: "pre-wrap",
    fontSize: 14,
  },
};