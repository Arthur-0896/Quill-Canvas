import React, { useEffect, useState } from "react";

export default function StoryEditor() {
  const [text, setText] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [hasTriggered, setHasTriggered] = useState(false);

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
    setImageUrl("");

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

      // 🔥 IMPORTANT: backend now returns image_url
      setImageUrl(data.image_url || "");
    } catch (err) {
      console.error("🔴 Fetch error:", err);
      setImageUrl("");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setHasTriggered(false);
    setImageUrl("");
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
            Generate Image
          </button>

          <button onClick={handleReset} style={styles.buttonSecondary}>
            Reset
          </button>
        </div>
      </div>

      {/* RIGHT */}
      <div style={styles.right}>
        {loading ? (
          <p>Generating image...</p>
        ) : imageUrl ? (
          <img
            src={imageUrl}
            style={styles.image}
            alt="Generated scene"
          />
        ) : (
          <p>Image will appear here</p>
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
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
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
  image: {
    maxWidth: "90%",
    maxHeight: "90%",
    borderRadius: 8,
    boxShadow: "0 4px 20px rgba(0,0,0,0.2)",
  },
};