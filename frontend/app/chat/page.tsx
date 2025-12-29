"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import styles from "./chat.module.css";

interface Message {
    id: number;
    role: "user" | "assistant";
    content: string;
    toolOutputs?: string[];
    files?: { name: string; type: string }[];
}

interface Chat {
    id: number;
    title: string;
    created_at: string;
}

interface UploadedFile {
    id: number;
    filename: string;
    original_filename: string;
    file_type: string;
}

export default function ChatPage() {
    const router = useRouter();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // State
    const [chats, setChats] = useState<Chat[]>([]);
    const [currentChatId, setCurrentChatId] = useState<number | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [showUpload, setShowUpload] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
    const [uploadingFile, setUploadingFile] = useState(false);
    const [expandedThinking, setExpandedThinking] = useState<number | null>(null);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isInitialLoading, setIsInitialLoading] = useState(true);

    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

    // Auto-dismiss error after 5 seconds
    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => setError(null), 5000);
            return () => clearTimeout(timer);
        }
    }, [error]);
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    // Extract downloadable files from message content (PDF, Word, Audio, etc.)
    const extractDownloadableFiles = (content: string): { filename: string; downloadLink: string; type: string }[] => {
        const files: { filename: string; downloadLink: string; type: string }[] = [];

        // Clean markdown formatting from content (**, *, etc.)
        const cleanMarkdown = (text: string) => text.replace(/\*+/g, '').trim();

        // Match new format [FILE]: filename [DOWNLOAD_LINK]: /api/files/download/filename
        const newFormatRegex = /\[FILE\]:\s*([^\n]+\.(pdf|docx|doc|pptx|ppt|wav|mp3))[\s\S]*?\[DOWNLOAD_LINK\]:\s*([^\n\s]+)/gi;
        let match;
        while ((match = newFormatRegex.exec(content)) !== null) {
            // Clean markdown from filename and link
            const filename = cleanMarkdown(match[1]);
            const ext = match[2].toLowerCase();
            const downloadLink = cleanMarkdown(match[3]);
            if (!files.find(f => f.filename === filename)) {
                let type = 'file';
                if (ext === 'pdf') type = 'pdf';
                else if (ext === 'docx' || ext === 'doc') type = 'word';
                else if (ext === 'wav' || ext === 'mp3') type = 'audio';
                else if (ext === 'pptx' || ext === 'ppt') type = 'pptx';
                files.push({ filename, downloadLink, type });
            }
        }

        return files;
    };

    // Get icon for file type
    const getFileIcon = (type: string) => {
        switch (type) {
            case 'pdf': return '📄';
            case 'word': return '📝';
            case 'audio': return '🔊';
            case 'pptx': return '📊';
            default: return '📁';
        }
    };

    // Download research paper
    const downloadResearchPaper = (downloadLink: string) => {
        // If it's a relative link, prepend API_URL
        const fullUrl = downloadLink.startsWith('/') ? `${API_URL}${downloadLink}` : downloadLink;
        window.open(fullUrl, '_blank');
    };

    // Auth check
    useEffect(() => {
        if (!token) {
            router.push("/auth");
        } else {
            fetchChats();
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token]);

    // Scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Fetch chats
    const fetchChats = async () => {
        try {
            setIsInitialLoading(true);
            const res = await fetch(`${API_URL}/api/chat/list`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setChats(data.chats);
            } else if (res.status === 401) {
                localStorage.removeItem("token");
                router.push("/auth");
            }
        } catch (err) {
            console.error("Failed to fetch chats:", err);
            setError("Failed to load chats. Please refresh the page.");
        } finally {
            setIsInitialLoading(false);
        }
    };

    // Create new chat
    const createNewChat = async () => {
        try {
            const res = await fetch(`${API_URL}/api/chat/new`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ title: "New Chat" }),
            });
            if (res.ok) {
                const chat = await res.json();
                setChats([chat, ...chats]);
                setCurrentChatId(chat.id);
                setMessages([]);
                setUploadedFiles([]);
            }
        } catch (err) {
            console.error("Failed to create chat:", err);
        }
    };

    // Load chat messages
    const loadChat = async (chatId: number) => {
        setCurrentChatId(chatId);
        try {
            const res = await fetch(`${API_URL}/api/chat/${chatId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (res.ok) {
                const data = await res.json();
                setMessages(
                    data.messages.map((m: any) => ({
                        ...m,
                        toolOutputs: m.tool_outputs ? JSON.parse(m.tool_outputs) : [],
                    }))
                );
            }
        } catch (err) {
            console.error("Failed to load chat:", err);
        }
    };

    // Delete chat
    const deleteChat = async (chatId: number, e: React.MouseEvent) => {
        e.stopPropagation();

        // Confirmation dialog
        const confirmed = window.confirm("Are you sure you want to delete this chat? This action cannot be undone.");
        if (!confirmed) return;

        try {
            await fetch(`${API_URL}/api/chat/${chatId}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` },
            });
            setChats(chats.filter((c) => c.id !== chatId));
            if (currentChatId === chatId) {
                setCurrentChatId(null);
                setMessages([]);
            }
        } catch (err) {
            console.error("Failed to delete chat:", err);
            alert("Failed to delete chat. Please try again.");
        }
    };

    // Send message
    const sendMessage = async () => {
        if (!input.trim() && uploadedFiles.length === 0) return;

        let chatIdToUse = currentChatId;
        if (!chatIdToUse) {
            // Create new chat and get the ID
            try {
                const res = await fetch(`${API_URL}/api/chat/new`, {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ title: "New Chat" }),
                });
                if (res.ok) {
                    const chat = await res.json();
                    setChats((prev) => [chat, ...prev]);
                    setCurrentChatId(chat.id);
                    chatIdToUse = chat.id;
                } else {
                    console.error("Failed to create chat");
                    return;
                }
            } catch (err) {
                console.error("Failed to create chat:", err);
                return;
            }
        }

        const userMessage: Message = {
            id: Date.now(),
            role: "user",
            content: input,
            files: uploadedFiles.map((f) => ({ name: f.original_filename, type: f.file_type })),
        };

        setMessages([...messages, userMessage]);
        setInput("");
        setLoading(true);

        try {
            const res = await fetch(`${API_URL}/api/chat/${chatIdToUse}/message`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    content: input,
                    file_ids: uploadedFiles.map((f) => f.id),
                }),
            });

            const reader = res.body?.getReader();
            const decoder = new TextDecoder();
            let assistantMessage: Message = {
                id: Date.now() + 1,
                role: "assistant",
                content: "",
                toolOutputs: [],
            };

            setMessages((prev) => [...prev, assistantMessage]);

            while (reader) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split("\n").filter((l) => l.startsWith("data:"));

                for (const line of lines) {
                    try {
                        const data = JSON.parse(line.replace("data: ", ""));
                        if (data.type === "tool") {
                            assistantMessage.toolOutputs = [
                                ...(assistantMessage.toolOutputs || []),
                                data.content,
                            ];
                        } else if (data.type === "response") {
                            assistantMessage.content = data.content;
                        }
                        setMessages((prev) =>
                            prev.map((m) => (m.id === assistantMessage.id ? { ...assistantMessage } : m))
                        );
                    } catch { }
                }
            }

            setUploadedFiles([]);
            fetchChats();
        } catch (err) {
            console.error("Failed to send message:", err);
        } finally {
            setLoading(false);
        }
    };

    // File upload
    const handleFileUpload = async (file: File, fileType: string) => {
        setUploadingFile(true);
        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("file_type", fileType);

            const res = await fetch(`${API_URL}/api/files/upload`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                body: formData,
            });

            if (res.ok) {
                const uploaded = await res.json();
                setUploadedFiles([...uploadedFiles, uploaded]);
                setShowUpload(false);
            }
        } catch (err) {
            console.error("Failed to upload file:", err);
        } finally {
            setUploadingFile(false);
        }
    };

    // Logout
    const handleLogout = () => {
        localStorage.removeItem("token");
        router.push("/");
    };

    // Convert response to file (Word/PDF/Voice/PPT)
    const convertToFile = async (messageContent: string, type: "word" | "pdf" | "voice" | "ppt") => {
        if (!currentChatId || !messageContent) return;

        setLoading(true);

        // Create a prompt to convert the content
        const prompts: Record<string, string> = {
            word: `Convert this to a Word document and give me download link:\n\n${messageContent}`,
            pdf: `Convert this to a PDF document and give me download link:\n\n${messageContent}`,
            voice: `Convert this to an audio file and give me download link:\n\n${messageContent}`,
            ppt: `Convert this to a PowerPoint and give me download link:\n\n${messageContent}`,
        };

        try {
            const res = await fetch(`${API_URL}/api/chat/${currentChatId}/message`, {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    content: prompts[type],
                    file_ids: [],
                }),
            });

            const reader = res.body?.getReader();
            const decoder = new TextDecoder();
            let assistantMessage: Message = {
                id: Date.now(),
                role: "assistant",
                content: "",
                toolOutputs: [],
            };

            setMessages((prev) => [...prev, assistantMessage]);

            while (reader) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split("\n").filter((l) => l.startsWith("data:"));

                for (const line of lines) {
                    try {
                        const data = JSON.parse(line.replace("data: ", ""));
                        if (data.type === "tool") {
                            assistantMessage.toolOutputs = [
                                ...(assistantMessage.toolOutputs || []),
                                data.content,
                            ];
                        } else if (data.type === "response") {
                            assistantMessage.content = data.content;
                        }
                        setMessages((prev) =>
                            prev.map((m) => (m.id === assistantMessage.id ? { ...assistantMessage } : m))
                        );
                    } catch { }
                }
            }
        } catch (err) {
            console.error("Failed to convert:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className={styles.main}>
            {/* Error Toast */}
            {error && (
                <div className={styles.errorToast}>
                    <span>⚠️ {error}</span>
                    <button onClick={() => setError(null)}>✕</button>
                </div>
            )}

            {/* Sidebar */}
            <aside className={`${styles.sidebar} ${sidebarOpen ? styles.open : ""}`}>
                <div className={styles.sidebarHeader}>
                    <div className={styles.logo}>
                        <span>🧠</span>
                        <span>Research Agent</span>
                    </div>
                    <button className={styles.toggleSidebar} onClick={() => setSidebarOpen(!sidebarOpen)}>
                        ☰
                    </button>
                </div>

                <button className={styles.newChatBtn} onClick={createNewChat}>
                    ➕ New Chat
                </button>

                <div className={styles.chatList}>
                    {isInitialLoading ? (
                        // Loading skeletons
                        <>
                            <div className={`${styles.skeleton} ${styles.chatSkeleton}`}></div>
                            <div className={`${styles.skeleton} ${styles.chatSkeleton}`}></div>
                            <div className={`${styles.skeleton} ${styles.chatSkeleton}`}></div>
                        </>
                    ) : chats.length === 0 ? (
                        <div className={styles.noChatMessage}>
                            <p>No chats yet</p>
                            <small>Click "New Chat" to start</small>
                        </div>
                    ) : (
                        chats.map((chat) => (
                            <div
                                key={chat.id}
                                className={`${styles.chatItem} ${currentChatId === chat.id ? styles.active : ""}`}
                                onClick={() => loadChat(chat.id)}
                            >
                                <span className={styles.chatIcon}>💬</span>
                                <span className={styles.chatTitle}>{chat.title}</span>
                                <button className={styles.deleteBtn} onClick={(e) => deleteChat(chat.id, e)}>
                                    ✕
                                </button>
                            </div>
                        ))
                    )}
                </div>

                <div className={styles.sidebarFooter}>
                    <button className={styles.logoutBtn} onClick={handleLogout}>
                        🚪 Logout
                    </button>
                </div>
            </aside>

            {/* Main Chat Area */}
            <div className={styles.chatArea}>
                {/* Toggle button when sidebar is closed */}
                {!sidebarOpen && (
                    <button
                        className={styles.floatingToggle}
                        onClick={() => setSidebarOpen(true)}
                    >
                        ☰
                    </button>
                )}
                {/* Messages */}
                <div className={styles.messages}>
                    {messages.length === 0 ? (
                        <div className={styles.emptyState}>
                            <div className={styles.emptyIcon}>🧠</div>
                            <h2>Research Agent</h2>
                            <p>Your AI-powered research assistant. Try these features:</p>
                            <div className={styles.suggestions}>
                                <button onClick={() => setInput("Find research papers about machine learning in healthcare")}>
                                    🔬 Search Papers
                                </button>
                                <button onClick={() => setInput("Summarize this paper in simple terms")}>
                                    📊 Summarize Paper
                                </button>
                                <button onClick={() => setInput("Generate APA citation for this paper")}>
                                    📝 Generate Citation
                                </button>
                                <button onClick={() => setInput("Compare these papers and find research gaps")}>
                                    🔍 Compare Papers
                                </button>
                                <button onClick={() => setInput("Write a literature review on AI")}>
                                    ✍️ Write Review
                                </button>
                                <button onClick={() => setShowUpload(true)}>
                                    📄 Upload Document
                                </button>
                            </div>
                        </div>
                    ) : (
                        messages.map((msg) => (
                            <div key={msg.id} className={`${styles.message} ${styles[msg.role]}`}>
                                <div className={styles.messageAvatar}>
                                    {msg.role === "user" ? "👤" : "🧠"}
                                </div>
                                <div className={styles.messageContent}>
                                    {/* Thinking Section */}
                                    {msg.role === "assistant" && msg.toolOutputs && msg.toolOutputs.length > 0 && (
                                        <div className={styles.thinkingSection}>
                                            <button
                                                className={styles.thinkingToggle}
                                                onClick={() => setExpandedThinking(expandedThinking === msg.id ? null : msg.id)}
                                            >
                                                🔍 Show Thinking ({msg.toolOutputs.length} steps)
                                                <span className={expandedThinking === msg.id ? styles.expanded : ""}>▼</span>
                                            </button>
                                            {expandedThinking === msg.id && (
                                                <div className={styles.thinkingContent}>
                                                    {msg.toolOutputs.map((output, i) => (
                                                        <div key={i} className={styles.toolOutput}>
                                                            {output}
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* Files */}
                                    {msg.files && msg.files.length > 0 && (
                                        <div className={styles.attachedFiles}>
                                            {msg.files.map((file, i) => (
                                                <span key={i} className={styles.fileChip}>
                                                    📎 {file.name}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    {/* Message Text */}
                                    <div className={styles.messageText}>{msg.content}</div>

                                    {/* Downloadable Files Buttons */}
                                    {msg.role === "assistant" && extractDownloadableFiles(msg.content).length > 0 && (
                                        <div className={styles.researchPapers}>
                                            <div className={styles.papersHeader}>📁 Download Files:</div>
                                            {extractDownloadableFiles(msg.content).map((file, i) => (
                                                <button
                                                    key={i}
                                                    className={styles.paperDownloadBtn}
                                                    onClick={() => downloadResearchPaper(file.downloadLink)}
                                                >
                                                    {getFileIcon(file.type)} {file.filename}
                                                </button>
                                            ))}
                                        </div>
                                    )}

                                    {/* Convert to File Options */}
                                    {msg.role === "assistant" && msg.content && (
                                        <div className={styles.downloadOptions}>
                                            <button
                                                onClick={() => convertToFile(msg.content, "word")}
                                                disabled={loading}
                                                title="Convert to Word document"
                                            >
                                                📝 Word
                                            </button>
                                            <button
                                                onClick={() => convertToFile(msg.content, "pdf")}
                                                disabled={loading}
                                                title="Convert to PDF document"
                                            >
                                                📄 PDF
                                            </button>
                                            <button
                                                onClick={() => convertToFile(msg.content, "ppt")}
                                                disabled={loading}
                                                title="Convert to PowerPoint presentation"
                                            >
                                                📊 PPT
                                            </button>
                                            <button
                                                onClick={() => convertToFile(msg.content, "voice")}
                                                disabled={loading}
                                                title="Convert to Audio file"
                                            >
                                                🔊 Voice
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                    {loading && (
                        <div className={`${styles.message} ${styles.assistant}`}>
                            <div className={styles.messageAvatar}>🧠</div>
                            <div className={styles.messageContent}>
                                <div className={styles.typing}>
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className={styles.inputArea}>
                    {/* Uploaded Files Preview */}
                    {uploadedFiles.length > 0 && (
                        <div className={styles.uploadedPreview}>
                            {uploadedFiles.map((file) => (
                                <span key={file.id} className={styles.fileChip}>
                                    📎 {file.original_filename}
                                    <button onClick={() => setUploadedFiles(uploadedFiles.filter(f => f.id !== file.id))}>✕</button>
                                </span>
                            ))}
                        </div>
                    )}

                    <div className={styles.inputWrapper}>
                        <button className={styles.uploadBtn} onClick={() => setShowUpload(true)} title="Upload file">
                            ➕
                        </button>
                        <input
                            type="text"
                            className={styles.input}
                            placeholder="Ask a research question... (Press Enter to send)"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                            disabled={loading}
                        />
                        <button
                            className={styles.sendBtn}
                            onClick={sendMessage}
                            disabled={loading || (!input.trim() && uploadedFiles.length === 0)}
                            title="Send message (Enter)"
                        >
                            {loading ? <span className="spinner"></span> : "➤"}
                        </button>
                    </div>
                    <div className={styles.inputHint}>
                        Press <kbd>Enter</kbd> to send, <kbd>Shift+Enter</kbd> for new line
                    </div>
                </div>
            </div>

            {/* File Upload Modal */}
            {showUpload && (
                <div className={styles.modalOverlay} onClick={() => setShowUpload(false)}>
                    <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                        <div className={styles.modalHeader}>
                            <h3>Upload File</h3>
                            <button onClick={() => setShowUpload(false)}>✕</button>
                        </div>
                        <div className={styles.uploadOptions}>
                            {[
                                { type: "pdf", icon: "📄", label: "PDF", accept: ".pdf" },
                                { type: "word", icon: "📝", label: "Word", accept: ".doc,.docx" },
                                { type: "pptx", icon: "📊", label: "PowerPoint", accept: ".ppt,.pptx" },
                                { type: "image", icon: "🖼️", label: "Image", accept: ".png,.jpg,.jpeg,.gif,.webp" },
                                { type: "audio", icon: "🎙️", label: "Audio", accept: ".mp3,.wav,.m4a,.ogg" },
                            ].map((opt) => (
                                <label key={opt.type} className={styles.uploadOption}>
                                    <input
                                        type="file"
                                        accept={opt.accept}
                                        onChange={(e) => {
                                            const file = e.target.files?.[0];
                                            if (file) handleFileUpload(file, opt.type);
                                        }}
                                        disabled={uploadingFile}
                                    />
                                    <div className={styles.uploadOptionContent}>
                                        <span className={styles.uploadIcon}>{opt.icon}</span>
                                        <span>{opt.label}</span>
                                    </div>
                                </label>
                            ))}
                        </div>
                        {uploadingFile && (
                            <div className={styles.uploadProgress}>
                                <span className="spinner"></span> Uploading...
                            </div>
                        )}
                    </div>
                </div>
            )}
        </main>
    );
}
