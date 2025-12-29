"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import styles from "./chat.module.css";
import { ToastProvider, useToast } from "@/components/Toast";
import { LoadingSpinner, ProgressBar, FileUploadProgress, PDFDownloadProgress } from "@/components/LoadingSpinner";

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

interface SearchResult {
    message_id: number;
    chat_id: number;
    chat_title: string;
    role: string;
    content: string;
    highlighted_content: string;
    created_at: string;
}

export default function ChatPage() {
    const router = useRouter();
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { success, error: showToastError } = useToast();

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

    // Search state
    const [showSearch, setShowSearch] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [isSearching, setIsSearching] = useState(false);

    // Upload progress state
    const [uploadProgress, setUploadProgress] = useState<{ filename: string; progress: number } | null>(null);

    // Shortcuts modal
    const [showShortcuts, setShowShortcuts] = useState(false);

    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const inputRef = useRef<HTMLInputElement>(null);

    // Auto-dismiss error after 5 seconds
    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => setError(null), 5000);
            return () => clearTimeout(timer);
        }
    }, [error]);

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Ignore shortcuts when typing in input
            if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
                // Ctrl+Enter to send
                if (e.ctrlKey && e.key === "Enter") {
                    e.preventDefault();
                    sendMessage();
                }
                return;
            }

            // Ctrl+N = New chat
            if (e.ctrlKey && e.key === "n") {
                e.preventDefault();
                createNewChat();
            }

            // Ctrl+/ = Show shortcuts
            if (e.ctrlKey && e.key === "/") {
                e.preventDefault();
                setShowShortcuts(true);
            }

            // Escape = Close modals
            if (e.key === "Escape") {
                setShowUpload(false);
                setShowSearch(false);
                setShowShortcuts(false);
                inputRef.current?.focus();
            }
        };

        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, [currentChatId, input]); // eslint-disable-line react-hooks/exhaustive-deps

    // Extract downloadable files from message content
    const extractDownloadableFiles = (content: string): { filename: string; downloadLink: string; type: string }[] => {
        const files: { filename: string; downloadLink: string; type: string }[] = [];
        const cleanMarkdown = (text: string) => text.replace(/\*+/g, '').trim();
        const newFormatRegex = /\[FILE\]:\s*([^\n]+\.(pdf|docx|doc|pptx|ppt|wav|mp3))[\s\S]*?\[DOWNLOAD_LINK\]:\s*([^\n\s]+)/gi;
        let match;
        while ((match = newFormatRegex.exec(content)) !== null) {
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

    const getFileIcon = (type: string) => {
        switch (type) {
            case 'pdf': return '📄';
            case 'word': return '📝';
            case 'audio': return '🔊';
            case 'pptx': return '📊';
            default: return '📁';
        }
    };

    const downloadResearchPaper = (downloadLink: string) => {
        const fullUrl = downloadLink.startsWith('/') ? `${API_URL}${downloadLink}` : downloadLink;
        window.open(fullUrl, '_blank');
    };

    // Search messages
    const performSearch = useCallback(async () => {
        if (!searchQuery.trim()) {
            setSearchResults([]);
            return;
        }

        setIsSearching(true);
        try {
            const res = await fetch(
                `${API_URL}/api/chat/search?q=${encodeURIComponent(searchQuery)}`,
                {
                    headers: { Authorization: `Bearer ${token}` },
                }
            );

            if (res.ok) {
                const data = await res.json();
                setSearchResults(data.results || []);
            }
        } catch (err) {
            console.error("Search failed:", err);
            setSearchResults([]);
        } finally {
            setIsSearching(false);
        }
    }, [searchQuery, token, API_URL]);

    // Debounced search
    useEffect(() => {
        const timer = setTimeout(performSearch, 300);
        return () => clearTimeout(timer);
    }, [searchQuery, performSearch]);

    // Navigate to search result
    const goToSearchResult = (chatId: number) => {
        loadChat(chatId);
        setShowSearch(false);
        setSearchQuery("");
        setSearchResults([]);
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
        setUploadProgress({ filename: file.name, progress: 0 });

        // Simulate progress (actual progress would need XHR)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                setUploadProgress({ filename: file.name, progress });
            }
        }, 200);

        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("file_type", fileType);

            const res = await fetch(`${API_URL}/api/files/upload`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                body: formData,
            });

            clearInterval(progressInterval);
            setUploadProgress({ filename: file.name, progress: 100 });

            if (res.ok) {
                const uploaded = await res.json();
                setUploadedFiles([...uploadedFiles, uploaded]);
                setShowUpload(false);
                success(`File "${file.name}" uploaded successfully`);
            } else {
                showToastError("Failed to upload file");
            }
        } catch (err) {
            clearInterval(progressInterval);
            console.error("Failed to upload file:", err);
            showToastError("Failed to upload file. Please try again.");
        } finally {
            setUploadingFile(false);
            setTimeout(() => setUploadProgress(null), 500);
        }
    };

    // Logout
    const handleLogout = () => {
        localStorage.removeItem("token");
        router.push("/");
    };

    // Convert response to file
    const convertToFile = async (messageContent: string, type: "word" | "pdf" | "voice" | "ppt") => {
        if (!currentChatId || !messageContent) return;

        setLoading(true);
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
        <ToastProvider>
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
                    <div className={styles.sidebarActions}>
                        <button
                            className={styles.searchBtn}
                            onClick={() => setShowSearch(true)}
                            title="Search chats (Ctrl+/)"
                        >
                            🔍
                        </button>
                        <button className={styles.toggleSidebar} onClick={() => setSidebarOpen(!sidebarOpen)}>
                            ☰
                        </button>
                    </div>
                </div>

                <button className={styles.newChatBtn} onClick={createNewChat}>
                    ➕ New Chat
                </button>

                <div className={styles.chatList}>
                    {isInitialLoading ? (
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
                    <button className={styles.shortcutsBtn} onClick={() => setShowShortcuts(true)}>
                        ⌨️ Shortcuts
                    </button>
                    <button className={styles.logoutBtn} onClick={handleLogout}>
                        🚪 Logout
                    </button>
                </div>
            </aside>

            {/* Main Chat Area */}
            <div className={styles.chatArea}>
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
                                    Search Papers
                                </button>
                                <button onClick={() => setInput("Summarize this paper in simple terms")}>
                                    Summarize Paper
                                </button>
                                <button onClick={() => setInput("Generate APA citation for this paper")}>
                                    Generate Citation
                                </button>
                                <button onClick={() => setInput("Compare these papers and find research gaps")}>
                                    Compare Papers
                                </button>
                                <button onClick={() => setInput("Write a literature review on AI")}>
                                    Write Review
                                </button>
                                <button onClick={() => setShowUpload(true)}>
                                    Upload Document
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
                                    {msg.role === "assistant" && msg.toolOutputs && msg.toolOutputs.length > 0 && (
                                        <div className={styles.thinkingSection}>
                                            <button
                                                className={styles.thinkingToggle}
                                                onClick={() => setExpandedThinking(expandedThinking === msg.id ? null : msg.id)}
                                            >
                                                🤔 Show Thinking ({msg.toolOutputs.length} steps)
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

                                    {msg.files && msg.files.length > 0 && (
                                        <div className={styles.attachedFiles}>
                                            {msg.files.map((file, i) => (
                                                <span key={i} className={styles.fileChip}>
                                                    📎 {file.name}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    <div className={styles.messageText}>{msg.content}</div>

                                    {msg.role === "assistant" && extractDownloadableFiles(msg.content).length > 0 && (
                                        <div className={styles.researchPapers}>
                                            <div className={styles.papersHeader}>Download Files:</div>
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

                                    {msg.role === "assistant" && msg.content && (
                                        <div className={styles.downloadOptions}>
                                            <button onClick={() => convertToFile(msg.content, "word")} disabled={loading}>
                                                Word
                                            </button>
                                            <button onClick={() => convertToFile(msg.content, "pdf")} disabled={loading}>
                                                PDF
                                            </button>
                                            <button onClick={() => convertToFile(msg.content, "ppt")} disabled={loading}>
                                                PPT
                                            </button>
                                            <button onClick={() => convertToFile(msg.content, "voice")} disabled={loading}>
                                                Voice
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
                            📎
                        </button>
                        <input
                            ref={inputRef}
                            type="text"
                            className={styles.input}
                            placeholder="Ask a research question... (Enter to send)"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    sendMessage();
                                }
                            }}
                            disabled={loading}
                        />
                        <button
                            className={styles.sendBtn}
                            onClick={sendMessage}
                            disabled={loading || (!input.trim() && uploadedFiles.length === 0)}
                            title="Send message (Enter)"
                        >
                            {loading ? "⏳" : "➤"}
                        </button>
                    </div>
                    <div className={styles.inputHint}>
                        Press <kbd>Enter</kbd> to send, <kbd>Ctrl+Enter</kbd> for new line
                    </div>
                </div>
            </div>

            {/* Search Modal */}
            {showSearch && (
                <div className={styles.modalOverlay} onClick={() => setShowSearch(false)}>
                    <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                        <div className={styles.modalHeader}>
                            <h3>🔍 Search Chats</h3>
                            <button onClick={() => setShowSearch(false)}>✕</button>
                        </div>
                        <div className={styles.searchContent}>
                            <input
                                type="text"
                                className={styles.searchInput}
                                placeholder="Search messages..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                autoFocus
                            />
                            {isSearching && <div className={styles.searchLoading}>Searching...</div>}
                            {!isSearching && searchResults.length > 0 && (
                                <div className={styles.searchResults}>
                                    {searchResults.map((result, i) => (
                                        <div
                                            key={i}
                                            className={styles.searchResult}
                                            onClick={() => goToSearchResult(result.chat_id)}
                                        >
                                            <div className={styles.searchResultChat}>{result.chat_title}</div>
                                            <div
                                                className={styles.searchResultContent}
                                                dangerouslySetInnerHTML={{ __html: result.highlighted_content }}
                                            />
                                        </div>
                                    ))}
                                </div>
                            )}
                            {!isSearching && searchQuery && searchResults.length === 0 && (
                                <div className={styles.noResults}>No results found</div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* File Upload Modal */}
            {showUpload && (
                <div className={styles.modalOverlay} onClick={() => setShowUpload(false)}>
                    <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                        <div className={styles.modalHeader}>
                            <h3>📤 Upload File</h3>
                            <button onClick={() => setShowUpload(false)}>✕</button>
                        </div>
                        <div className={styles.uploadOptions}>
                            {[
                                { type: "pdf", icon: "📄", label: "PDF", accept: ".pdf" },
                                { type: "word", icon: "📝", label: "Word", accept: ".doc,.docx" },
                                { type: "pptx", icon: "📊", label: "PowerPoint", accept: ".ppt,.pptx" },
                                { type: "image", icon: "🖼️", label: "Image", accept: ".png,.jpg,.jpeg,.gif,.webp" },
                                { type: "audio", icon: "🔊", label: "Audio", accept: ".mp3,.wav,.m4a,.ogg" },
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
                        {uploadingFile && uploadProgress && (
                            <FileUploadProgress
                                filename={uploadProgress.filename}
                                progress={uploadProgress.progress}
                            />
                        )}
                    </div>
                </div>
            )}

            {/* Keyboard Shortcuts Modal */}
            {showShortcuts && (
                <div className={styles.modalOverlay} onClick={() => setShowShortcuts(false)}>
                    <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                        <div className={styles.modalHeader}>
                            <h3>⌨️ Keyboard Shortcuts</h3>
                            <button onClick={() => setShowShortcuts(false)}>✕</button>
                        </div>
                        <div className={styles.shortcutsList}>
                            <div className={styles.shortcutItem}>
                                <span className={styles.shortcutKey}>Enter</span>
                                <span className={styles.shortcutAction}>Send message</span>
                            </div>
                            <div className={styles.shortcutItem}>
                                <span className={styles.shortcutKey}>Ctrl + Enter</span>
                                <span className={styles.shortcutAction}>Send message</span>
                            </div>
                            <div className={styles.shortcutItem}>
                                <span className={styles.shortcutKey}>Ctrl + N</span>
                                <span className={styles.shortcutAction}>New chat</span>
                            </div>
                            <div className={styles.shortcutItem}>
                                <span className={styles.shortcutKey}>Ctrl + /</span>
                                <span className={styles.shortcutAction}>Search chats</span>
                            </div>
                            <div className={styles.shortcutItem}>
                                <span className={styles.shortcutKey}>Escape</span>
                                <span className={styles.shortcutAction}>Close modals</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </main>
        </ToastProvider>
    );
}
