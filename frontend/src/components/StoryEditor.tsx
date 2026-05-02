import React, { useState, useEffect } from "react";

export default function QuillCanvas() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentView, setCurrentView] = useState<"writer" | "generating" | "storybook">("writer");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  const [storyTitle, setStoryTitle] = useState("The Weatherman's Letters");
  const [storyText, setStoryText] = useState("");
  const [wordCount, setWordCount] = useState(0);
  
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  
  const [generatedImageUrl, setGeneratedImageUrl] = useState("");
  const [generatedPrompt, setGeneratedPrompt] = useState("");
  const [generationId, setGenerationId] = useState("");

  const API_URL = "http://localhost:8000";

  const steps = [
    "Analyzing your story",
    "Creating prompt for illustration",
    "Generating artwork",
    "Finalizing your storybook"
  ];

  useEffect(() => {
    // Load demo story
    const demoStory = `For thirty years, Marcus predicted the weather with uncanny accuracy. Never wrong. Not once.

His colleagues assumed satellites and algorithms. They didn't know about the letters.

Every evening, Marcus received an envelope slipped under his door. Inside: tomorrow's weather, written in elegant script. No signature. No return address.

He'd tried everything—cameras, stakeouts, moving apartments. The letters always found him.

Tonight, the envelope felt different. Heavier.

Inside, a final forecast and a note:

"I'm dying, Marcus. Forty years ago, I was the weatherman you replaced. I made one catastrophic mistake—told people it would be sunny. A tornado killed seventeen, including my daughter at her outdoor wedding.

I found an old woman who claimed she could see tomorrow. Desperate, I paid her everything. She gave me predictions for the next forty years. Every single day.

I've spent my life making sure no weatherman would fail like I did. The last prediction is yours for tomorrow. After that, you're on your own.

Trust the science. But more importantly, trust that people will forgive honest mistakes made with care."

The next morning, Marcus delivered his first independent forecast.

It was wrong.

And he was finally free.`;
    
    setStoryText(demoStory);
    updateWordCount(demoStory);
  }, []);

  const updateWordCount = (text: string) => {
    const trimmed = text.trim();
    const count = trimmed ? trimmed.split(/\s+/).length : 0;
    setWordCount(count);
  };

  const handleTextChange = (text: string) => {
    setStoryText(text);
    updateWordCount(text);
  };

  const doLogin = () => {
    setIsLoggedIn(true);
  };

  const generateStory = async () => {
    if (!storyText.trim()) {
      setError("Please write a story first!");
      return;
    }

    setLoading(true);
    setError("");
    setProgress(0);
    setCurrentStep(0);
    setCurrentView("generating");

    try {
      // Step 1: Analyzing
      setProgress(25);
      setCurrentStep(0);

      const response = await fetch(`${API_URL}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ story: storyText }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Generation failed");
      }

      const data = await response.json();

      // Step 2: Prompt created
      setProgress(50);
      setCurrentStep(1);
      setGeneratedPrompt(data.prompt || "");

      // Step 3: Image generating
      setProgress(75);
      setCurrentStep(2);
      setGeneratedImageUrl(data.image_url || "");
      setGenerationId(data.generation_id || "");

      // Step 4: Complete
      setProgress(100);
      setCurrentStep(3);

      setTimeout(() => {
        setCurrentView("storybook");
        setLoading(false);
      }, 500);

    } catch (err) {
      console.error("Generation error:", err);
      setError(err instanceof Error ? err.message : "Failed to generate story");
      setCurrentView("writer");
      setLoading(false);
    }
  };

  const downloadPDF = async () => {
    if (!storyText || !generatedImageUrl) {
      setError("Please generate a storybook first!");
      return;
    }

    try {
      setPdfLoading(true);

      const response = await fetch(`${API_URL}/generate-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          story: storyText,
          image_url: generatedImageUrl,
          prompt: generatedPrompt,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "PDF generation failed");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${storyTitle || "story"}_${Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (err) {
      console.error("PDF error:", err);
      setError(err instanceof Error ? err.message : "Failed to generate PDF");
    } finally {
      setPdfLoading(false);
    }
  };

  const resetStory = () => {
    setStoryText("");
    setStoryTitle("Untitled Story");
    setGeneratedImageUrl("");
    setGeneratedPrompt("");
    setGenerationId("");
    setWordCount(0);
    setCurrentView("writer");
  };

  if (!isLoggedIn) {
    return (
      <div style={styles.loginScreen}>
        <div style={styles.loginCard}>
          <div style={styles.loginLogo}>
            <div style={styles.logoMark}>✦</div>
            <div style={styles.logoWordmark}>
              <div style={styles.logoName}>
                Quill<span style={{ color: "#16A34A" }}>Canvas</span>
              </div>
              <div style={styles.logoTagline}>AI STORYBOOK WRITER</div>
            </div>
          </div>

          <h1 style={styles.loginHeading}>Welcome back</h1>
          <p style={styles.loginSub}>Sign in to continue creating magical stories</p>

          <button style={styles.btnGuest} onClick={doLogin}>
            Continue as Guest
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.app}>
      {/* Sidebar Overlay */}
      {sidebarOpen && (
        <div style={styles.sidebarOverlay} onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside style={{ ...styles.sidebar, ...(sidebarOpen ? styles.sidebarOpen : {}) }}>
        <div style={styles.sidebarLogo}>
          <div style={styles.logoMark}>✦</div>
          <div style={styles.logoWordmark}>
            <div style={styles.logoName}>
              Quill<span style={{ color: "#16A34A" }}>Canvas</span>
            </div>
            <div style={styles.logoTagline}>AI STORYBOOK WRITER</div>
          </div>
        </div>

        <div style={styles.sidebarActions}>
          <button style={styles.btnNewStory} onClick={resetStory}>
            ✦ New Story
          </button>
        </div>

        <div style={styles.sidebarSection}>
          <div style={styles.sectionLabel}>Recent Stories</div>
          <div style={styles.storyItem}>
            <span style={styles.storyDot}></span>
            <span>The Weatherman's Letters</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main style={styles.main}>
        {/* Topbar */}
        <div style={styles.topbar}>
          <button
            style={styles.btnHamburger}
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            ☰
          </button>

          <input
            style={styles.titleInput}
            value={storyTitle}
            onChange={(e) => setStoryTitle(e.target.value)}
            placeholder="Untitled Story"
          />

          <div style={styles.actionsRow}>
            {generatedImageUrl && (
              <button
                style={{ ...styles.btnAct, ...styles.btnSecondary }}
                onClick={downloadPDF}
                disabled={pdfLoading}
              >
                {pdfLoading ? "Creating PDF..." : "📄 Download PDF"}
              </button>
            )}
            <button
              style={styles.btnAct}
              onClick={generateStory}
              disabled={loading || !storyText.trim()}
            >
              ✨ Generate Story
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div style={styles.contentArea}>
          {/* Error Message */}
          {error && (
            <div style={styles.errorBox}>
              <strong>⚠️ Error:</strong> {error}
              <button style={styles.errorClose} onClick={() => setError("")}>
                ✕
              </button>
            </div>
          )}

          {/* Writer View */}
          {currentView === "writer" && (
            <div style={styles.view}>
              <div style={styles.writerBox}>
                <div style={styles.writerLabel}>
                  <span>Your Story</span>
                  <span style={styles.wordCount}>
                    {wordCount} {wordCount === 1 ? "word" : "words"}
                  </span>
                </div>
                <textarea
                  style={styles.textarea}
                  value={storyText}
                  onChange={(e) => handleTextChange(e.target.value)}
                  placeholder="Start writing your story here..."
                />
              </div>
            </div>
          )}

          {/* Generating View */}
          {currentView === "generating" && (
            <div style={styles.view}>
              <div style={styles.genProgress}>
                <h2 style={styles.genTitle}>✨ Generating Your Story</h2>
                <p style={styles.genSub}>
                  Please wait while AI creates your storybook...
                </p>

                <div style={styles.progressBar}>
                  <div style={{ ...styles.progressFill, width: `${progress}%` }} />
                </div>

                <div style={styles.genSteps}>
                  {steps.map((step, idx) => (
                    <div
                      key={idx}
                      style={{
                        ...styles.genStep,
                        ...(idx === currentStep ? styles.genStepActive : {}),
                        ...(idx < currentStep ? styles.genStepDone : {}),
                      }}
                    >
                      <span style={styles.genStepIcon}>
                        {idx < currentStep ? "✓" : idx === currentStep ? "●" : "○"}
                      </span>
                      <span>{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Storybook View */}
          {currentView === "storybook" && (
            <div style={styles.view}>
              <div style={styles.bookDisplay}>
                <div style={styles.bookSpread}>
                  <div style={styles.bookPage}>
                    <div style={styles.pageText}>{storyText}</div>
                  </div>
                  <div style={styles.bookPage}>
                    {generatedImageUrl ? (
                      <img
                        src={generatedImageUrl}
                        alt="Generated illustration"
                        style={styles.pageImg}
                      />
                    ) : (
                      <div style={styles.imgPlaceholder}>No image generated</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  loginScreen: {
    position: "fixed",
    inset: 0,
    background: "#F7FDF9",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "16px",
  },
  loginCard: {
    background: "#FFFFFF",
    border: "1px solid #E4EDE8",
    borderRadius: "24px",
    padding: "40px",
    width: "100%",
    maxWidth: "400px",
    boxShadow: "0 24px 64px rgba(0,0,0,.14)",
  },
  loginLogo: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    marginBottom: "28px",
  },
  logoMark: {
    width: "36px",
    height: "36px",
    background: "#166534",
    borderRadius: "8px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#fff",
    fontSize: "20px",
    flexShrink: 0,
  },
  logoWordmark: {
    display: "flex",
    flexDirection: "column",
    gap: "2px",
  },
  logoName: {
    fontSize: "16px",
    fontWeight: 700,
    letterSpacing: "-.4px",
    color: "#0F1C14",
  },
  logoTagline: {
    fontSize: "10px",
    color: "#8FA89A",
    letterSpacing: ".2px",
  },
  loginHeading: {
    fontSize: "22px",
    fontWeight: 700,
    letterSpacing: "-.4px",
    marginBottom: "6px",
  },
  loginSub: {
    fontSize: "13px",
    color: "#8FA89A",
    marginBottom: "28px",
  },
  btnGuest: {
    width: "100%",
    background: "none",
    border: "1px solid #E4EDE8",
    borderRadius: "8px",
    padding: "12px",
    cursor: "pointer",
    fontSize: "13px",
    fontWeight: 500,
    color: "#4B6155",
    transition: "all .15s",
  },
  app: {
    display: "flex",
    width: "100%",
    height: "100vh",
    overflow: "hidden",
    fontFamily: "Inter, sans-serif",
    background: "#F7FDF9",
  },
  sidebarOverlay: {
    display: "block",
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,.4)",
    zIndex: 99,
  },
  sidebar: {
    width: "248px",
    height: "100%",
    background: "#FFFFFF",
    borderRight: "1px solid #E4EDE8",
    display: "flex",
    flexDirection: "column",
    flexShrink: 0,
    zIndex: 100,
    transition: "transform .22s ease",
  },
  sidebarOpen: {
    transform: "translateX(0)",
  },
  sidebarLogo: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "18px 20px",
    borderBottom: "1px solid #E4EDE8",
  },
  sidebarActions: {
    padding: "14px 12px",
  },
  btnNewStory: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    width: "100%",
    padding: "9px 14px",
    background: "#16A34A",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
    transition: "background .15s",
  },
  sidebarSection: {
    flex: 1,
    padding: "8px 12px 0",
    overflowY: "auto",
  },
  sectionLabel: {
    fontSize: "10px",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: ".8px",
    color: "#8FA89A",
    padding: "0 6px",
    marginBottom: "6px",
  },
  storyItem: {
    display: "flex",
    alignItems: "center",
    gap: "9px",
    padding: "8px 10px",
    borderRadius: "8px",
    fontSize: "13px",
    color: "#4B6155",
    cursor: "pointer",
    background: "#DCFCE7",
    fontWeight: 500,
  },
  storyDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    background: "#4ADE80",
    flexShrink: 0,
  },
  main: {
    flex: 1,
    height: "100%",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    minWidth: 0,
  },
  topbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "12px",
    padding: "18px 40px",
    background: "#FFFFFF",
    borderBottom: "1px solid #E4EDE8",
  },
  btnHamburger: {
    display: "none",
    width: "32px",
    height: "32px",
    border: "1px solid #E4EDE8",
    background: "#fff",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "16px",
    color: "#4B6155",
  },
  titleInput: {
    flex: 1,
    fontSize: "16px",
    fontWeight: 600,
    border: "none",
    outline: "none",
    background: "transparent",
    color: "#0F1C14",
    padding: "4px 8px",
    borderRadius: "8px",
  },
  actionsRow: {
    display: "flex",
    gap: "8px",
    alignItems: "center",
  },
  btnAct: {
    padding: "8px 14px",
    background: "#16A34A",
    color: "#fff",
    border: "none",
    borderRadius: "8px",
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
    transition: "background .15s",
    whiteSpace: "nowrap",
  },
  btnSecondary: {
    background: "#fff",
    color: "#15803D",
    border: "1px solid #86EFAC",
  },
  contentArea: {
    flex: 1,
    overflowY: "auto",
    padding: "40px",
  },
  errorBox: {
    background: "#FEE2E2",
    border: "1px solid #DC2626",
    borderRadius: "12px",
    padding: "16px",
    marginBottom: "20px",
    fontSize: "14px",
    color: "#991B1B",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  errorClose: {
    background: "none",
    border: "none",
    fontSize: "18px",
    cursor: "pointer",
    color: "#DC2626",
  },
  view: {
    display: "block",
  },
  writerBox: {
    background: "#FFFFFF",
    border: "1px solid #E4EDE8",
    borderRadius: "16px",
    padding: "24px",
  },
  writerLabel: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    fontSize: "13px",
    fontWeight: 500,
    color: "#4B6155",
    marginBottom: "12px",
  },
  wordCount: {
    fontSize: "11px",
    color: "#8FA89A",
    fontWeight: 400,
  },
  textarea: {
    width: "100%",
    minHeight: "500px",
    padding: "16px",
    border: "1px solid #E4EDE8",
    borderRadius: "12px",
    fontSize: "14px",
    lineHeight: 1.8,
    color: "#0F1C14",
    background: "#F7FDF9",
    resize: "vertical",
    outline: "none",
    fontFamily: "Inter, sans-serif",
  },
  genProgress: {
    background: "#FFFFFF",
    border: "1px solid #E4EDE8",
    borderRadius: "16px",
    padding: "32px",
    textAlign: "center",
  },
  genTitle: {
    fontSize: "20px",
    fontWeight: 600,
    marginBottom: "12px",
  },
  genSub: {
    color: "#8FA89A",
    fontSize: "13px",
    marginBottom: "20px",
  },
  progressBar: {
    width: "100%",
    height: "8px",
    background: "#DCFCE7",
    borderRadius: "4px",
    overflow: "hidden",
    margin: "20px 0",
  },
  progressFill: {
    height: "100%",
    background: "#16A34A",
    transition: "width .3s",
  },
  genSteps: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    marginTop: "24px",
  },
  genStep: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    fontSize: "13px",
    color: "#8FA89A",
  },
  genStepActive: {
    color: "#15803D",
    fontWeight: 500,
  },
  genStepDone: {
    color: "#16A34A",
  },
  genStepIcon: {
    fontSize: "14px",
  },
  bookDisplay: {
    background: "#FFFFFF",
    border: "1px solid #E4EDE8",
    borderRadius: "16px",
    padding: "32px",
  },
  bookSpread: {
    display: "flex",
    gap: "20px",
  },
  bookPage: {
    flex: 1,
    background: "#fff",
    border: "1px solid #ddd",
    borderRadius: "8px",
    padding: "24px",
    minHeight: "500px",
    boxShadow: "0 2px 8px rgba(0,0,0,.05)",
  },
  pageText: {
    fontSize: "14px",
    lineHeight: 1.8,
    color: "#333",
    whiteSpace: "pre-wrap",
  },
  pageImg: {
    width: "100%",
    height: "auto",
    borderRadius: "8px",
  },
  imgPlaceholder: {
    background: "#f5f5f5",
    border: "2px dashed #ccc",
    borderRadius: "8px",
    padding: "40px",
    textAlign: "center",
    color: "#999",
    minHeight: "400px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
};