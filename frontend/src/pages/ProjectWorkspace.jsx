import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiFetch, apiFetchRaw } from "../lib/api.js";
import { streamChat } from "../lib/stream.js";

export default function ProjectWorkspace() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [activeCitations, setActiveCitations] = useState([]);
  const [selectedText, setSelectedText] = useState(null);
  const [selectedMeta, setSelectedMeta] = useState(null);
  const [selectedDocName, setSelectedDocName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const loadProject = async () => {
    const data = await apiFetch(`/projects/${projectId}`);
    setProject(data);
  };

  const loadDocuments = async () => {
    const data = await apiFetch(`/projects/${projectId}/documents`);
    setDocuments(data);
  };

  const loadHistory = async () => {
    const data = await apiFetch(`/projects/${projectId}/chat`);
    const formatted = data.map((msg) => ({
      role: msg.role,
      content: msg.content,
      citations: msg.sources_json || [],
    }));
    setMessages(formatted);
    const lastAssistant = formatted.filter((msg) => msg.role === "assistant").pop();
    setActiveCitations(lastAssistant?.citations || []);
  };

  useEffect(() => {
    Promise.all([loadProject(), loadDocuments(), loadHistory()]).catch((err) =>
      setError(err.message)
    );
  }, [projectId]);

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      await apiFetch(`/projects/${projectId}/documents/upload`, {
        method: "POST",
        body: formData,
      });
      await loadDocuments();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleUrlIngest = async (event) => {
    event.preventDefault();
    if (!urlInput) return;
    try {
      await apiFetch(`/projects/${projectId}/documents/url`, {
        method: "POST",
        body: JSON.stringify({ url: urlInput }),
      });
      setUrlInput("");
      await loadDocuments();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAsk = async (event) => {
    event.preventDefault();
    if (!question.trim()) return;
    setError("");
    setLoading(true);
    const userMessage = { role: "user", content: question, citations: [] };
    const assistantMessage = { role: "assistant", content: "", citations: [] };
    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setQuestion("");

    try {
      const response = await apiFetchRaw(`/projects/${projectId}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage.content }),
      });
      let buffer = "";
      await streamChat(
        response,
        (token) => {
          buffer += token;
          setMessages((prev) => {
            const updated = [...prev];
            const lastIndex = updated.length - 1;
            updated[lastIndex] = { ...updated[lastIndex], content: buffer };
            return updated;
          });
        },
        (eventData) => {
          const citations = eventData.citations || [];
          setMessages((prev) => {
            const updated = [...prev];
            const lastIndex = updated.length - 1;
            updated[lastIndex] = { ...updated[lastIndex], citations };
            return updated;
          });
          setActiveCitations(citations);
        }
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      loadDocuments().catch(() => {});
    }
  };

  const viewText = async (documentId, name) => {
    try {
      const data = await apiFetch(`/projects/${projectId}/documents/${documentId}/text`);
      setSelectedText(data.text ?? "");
      setSelectedMeta(data.metadata || null);
      setSelectedDocName(name || "Document");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="workspace">
      <header className="topbar">
        <div>
          <button className="link" onClick={() => navigate("/dashboard")}>
            ← Back to dashboard
          </button>
          <h1>{project?.name || "Project workspace"}</h1>
          <p className="muted">{project?.description}</p>
        </div>
      </header>
      <div className="workspace-grid">
        <section className="panel">
          <h2>Sources</h2>
          <div className="upload-actions">
            <label className="file-input">
              Upload PDF or TXT
              <input type="file" accept=".pdf,.txt" onChange={handleUpload} />
            </label>
            <form onSubmit={handleUrlIngest} className="inline-form">
              <input
                placeholder="Paste article URL"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
              />
              <button className="secondary" type="submit">
                Add URL
              </button>
            </form>
          </div>
          <div className="doc-list">
            {documents.map((doc) => (
              <div key={doc.id} className="doc-row">
                <div>
                  <strong>{doc.name}</strong>
                  <div className="muted">
                    {doc.doc_type.toUpperCase()} · {doc.status}
                  </div>
                </div>
                <button className="link" onClick={() => viewText(doc.id, doc.name)}>
                  View text
                </button>
              </div>
            ))}
          </div>
          {selectedText !== null && (
            <div className="text-preview">
              <h3>Extracted text</h3>
              <p className="muted">{selectedDocName}</p>
              {selectedMeta?.error && (
                <p className="error">Extraction error: {selectedMeta.error}</p>
              )}
              {selectedText ? (
                <p>{selectedText}</p>
              ) : (
                <p className="muted">
                  No extractable text found. If this is a scanned PDF, upload an OCR version.
                </p>
              )}
            </div>
          )}
        </section>
        <section className="panel chat-panel">
          <h2>Ask your documents</h2>
          <div className="chat-history">
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-bubble ${msg.role}`}>
                <p>{msg.content}</p>
                {msg.role === "assistant" && msg.citations?.length > 0 && (
                  <div className="citation-inline">
                    {msg.citations.map((c, i) => (
                      <button
                        key={`${c.document_id}-${i}`}
                        className="citation-pill"
                        onClick={() => setActiveCitations(msg.citations)}
                      >
                        [{i + 1}] {c.document_name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
          <form onSubmit={handleAsk} className="chat-input">
            <input
              placeholder="Ask a question about your sources..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button className="primary" type="submit" disabled={loading}>
              {loading ? "Thinking..." : "Send"}
            </button>
          </form>
          {error && <div className="error">{error}</div>}
        </section>
        <section className="panel">
          <h2>Source citations</h2>
          {activeCitations.length === 0 && <p className="muted">Ask a question to see sources.</p>}
          {activeCitations.map((citation, index) => (
            <div key={`${citation.document_id}-${index}`} className="citation-card">
              <div className="citation-header">
                <span className="badge">[{index + 1}]</span>
                <strong>{citation.document_name}</strong>
              </div>
              <p className="muted">
                Page {citation.page_number || "N/A"}
              </p>
              <p>{citation.snippet}</p>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
