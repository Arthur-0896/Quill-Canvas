import React, { useState, useEffect, useRef, useCallback } from 'react';
import './StoryEditor.css';

interface Scene {
  scene_id: string;
  sequence: number;
  title: string;
  description: string;
  image_prompt: string;
  image_base64?: string;
  status: 'detecting' | 'generating' | 'completed' | 'error';
}

interface WebSocketMessage {
  type: 'scene_detected' | 'image_generating' | 'image_generated' | 'processing_completed' | 'processing_started' | 'error' | 'pong';
  [key: string]: any;
}

const StoryEditor: React.FC = () => {
  const [storyTitle, setStoryTitle] = useState('Untitled Story');
  const [storyContent, setStoryContent] = useState('');
  const [author, setAuthor] = useState('');
  const [scenes, setScenes] = useState<Map<string, Scene>>(new Map());
  const [isProcessing, setIsProcessing] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const ws = useRef<WebSocket | null>(null);
  const storyIdRef = useRef<string>('');
  const debounceTimerRef = useRef<NodeJS.Timeout>();

  // Initialize WebSocket
  useEffect(() => {
    if (!storyIdRef.current) {
      storyIdRef.current = `story-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/editor/ws/${storyIdRef.current}`;
    
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('✓ Connected to real-time editor');
      // Send keep-alive ping every 30 seconds
      setInterval(() => {
        if (ws.current?.readyState === WebSocket.OPEN) {
          ws.current?.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
    };

    ws.current.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      handleWebSocketMessage(message);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStatusMessage('Connection error');
    };

    ws.current.onclose = () => {
      console.log('WebSocket closed');
    };

    return () => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current?.close();
      }
    };
  }, []);

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'processing_started':
        setIsProcessing(true);
        setStatusMessage(message.message);
        break;

      case 'scene_detected':
        setScenes((prev) => {
          const updated = new Map(prev);
          updated.set(message.scene_id, {
            scene_id: message.scene_id,
            sequence: message.sequence,
            title: message.title,
            description: message.description,
            image_prompt: message.image_prompt,
            status: 'detecting',
          });
          return updated;
        });
        break;

      case 'image_generating':
        setScenes((prev) => {
          const updated = new Map(prev);
          const scene = updated.get(message.scene_id);
          if (scene) {
            scene.status = 'generating';
          }
          return updated;
        });
        setStatusMessage(message.message);
        break;

      case 'image_generated':
        setScenes((prev) => {
          const updated = new Map(prev);
          const scene = updated.get(message.scene_id);
          if (scene) {
            scene.image_base64 = message.image_base64;
            scene.status = 'completed';
          }
          return updated;
        });
        break;

      case 'processing_completed':
        setIsProcessing(false);
        setStatusMessage(`✓ ${message.message}`);
        break;

      case 'error':
        setIsProcessing(false);
        setStatusMessage(`✗ Error: ${message.error}`);
        break;
    }
  };

  // Debounced content update
  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    setStoryContent(newContent);

    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Debounce by 1.5 seconds
    debounceTimerRef.current = setTimeout(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current?.send(
          JSON.stringify({
            type: 'story_update',
            title: storyTitle,
            author: author,
            content: newContent,
          })
        );
      }
    }, 1500);
  };

  const currentScene =
    scenes.size > 0 ? Array.from(scenes.values()).sort((a, b) => a.sequence - b.sequence)[0] : null;

  return (
    <div className="story-editor">
      <header className="editor-header">
        <div className="header-controls">
          <input
            type="text"
            className="story-title-input"
            value={storyTitle}
            onChange={(e) => setStoryTitle(e.target.value)}
            placeholder="Story Title"
          />
          <input
            type="text"
            className="author-input"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="Author"
          />
        </div>
        <div className="status-bar">
          {statusMessage && <span className="status-message">{statusMessage}</span>}
          {isProcessing && <span className="processing-indicator">⏳ Processing...</span>}
        </div>
      </header>

      <div className="editor-container">
        {/* Left Pane: Story Editor */}
        <div className="editor-pane left-pane">
          <div className="pane-header">
            <h2>📝 Write Your Story</h2>
            <span className="word-count">{storyContent.split(/\s+/).filter(w => w).length} words</span>
          </div>
          <textarea
            className="story-textarea"
            value={storyContent}
            onChange={handleContentChange}
            placeholder="Start writing your story here... Images will generate as you type."
          />
        </div>

        {/* Divider */}
        <div className="editor-divider" />

        {/* Right Pane: Generated Images */}
        <div className="editor-pane right-pane">
          <div className="pane-header">
            <h2>🎨 Generated Images</h2>
            <span className="scene-count">{scenes.size} scenes</span>
          </div>

          {scenes.size === 0 ? (
            <div className="empty-state">
              <p>Images will appear here as you write...</p>
              <p className="hint">The AI will automatically detect scenes and generate images</p>
            </div>
          ) : (
            <div className="scenes-container">
              {currentScene && (
                <div className="current-scene">
                  <div className="scene-info">
                    <h3>{currentScene.title}</h3>
                    <p className="scene-description">{currentScene.description}</p>
                    <p className="scene-sequence">Scene {currentScene.sequence} of {scenes.size}</p>
                  </div>

                  <div className="image-container">
                    {currentScene.status === 'generating' && (
                      <div className="loading-skeleton">
                        <div className="shimmer" />
                        <p>Generating image...</p>
                      </div>
                    )}
                    {currentScene.image_base64 && (
                      <img
                        src={`data:image/png;base64,${currentScene.image_base64}`}
                        alt={currentScene.title}
                        className="generated-image"
                      />
                    )}
                    {currentScene.status === 'error' && (
                      <div className="error-state">
                        <p>Failed to generate image</p>
                      </div>
                    )}
                  </div>

                  {currentScene.sequence < scenes.size && (
                    <button className="next-scene-btn">Next Scene →</button>
                  )}
                </div>
              )}

              {/* Scene thumbnails */}
              <div className="scenes-gallery">
                <h4>All Scenes</h4>
                <div className="thumbnails">
                  {Array.from(scenes.values())
                    .sort((a, b) => a.sequence - b.sequence)
                    .map((scene) => (
                      <div key={scene.scene_id} className="thumbnail">
                        {scene.image_base64 ? (
                          <>
                            <img
                              src={`data:image/png;base64,${scene.image_base64}`}
                              alt={scene.title}
                            />
                            <span className="scene-num">{scene.sequence}</span>
                          </>
                        ) : (
                          <div className="thumbnail-placeholder">
                            <span>Scene {scene.sequence}</span>
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StoryEditor;
