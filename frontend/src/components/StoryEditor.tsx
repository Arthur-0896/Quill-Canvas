import React from "react";

export default function StoryEditor() {
  return (
    <div style={styles.container}>
      {/* Left side: Text */}
      <div style={styles.left}>
        <h1 style={styles.heading}>Your Title Here</h1>
        <p style={styles.paragraph}>
          This is where your text content goes. You can describe your product,
          idea, or any information you want to show on the left side of the page.
        </p>
        <p style={styles.paragraph}>
          You can add more paragraphs, lists, or anything else you need.
        </p>
      </div>

      {/* Right side: Image placeholder */}
      <div style={styles.right}>
        <div style={styles.imagePlaceholder}>
          Image Placeholder
        </div>
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
    justifyContent: "center",
    backgroundColor: "#f9f9f9",
  },
  right: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#eaeaea",
  },
  heading: {
    fontSize: "32px",
    marginBottom: "20px",
  },
  paragraph: {
    fontSize: "16px",
    lineHeight: 1.6,
    marginBottom: "12px",
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
  },
};