"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import styles from "./auth.module.css";

export default function AuthPage() {
    const router = useRouter();
    const [isLogin, setIsLogin] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const [formData, setFormData] = useState({
        email: "",
        password: "",
        name: "",
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setError("");
    };

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const endpoint = isLogin ? "/api/auth/login" : "/api/auth/signup";
            const body = isLogin
                ? { email: formData.email, password: formData.password }
                : formData;

            const response = await fetch(`${API_URL}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Authentication failed");
            }

            // Save token
            localStorage.setItem("token", data.access_token);

            // Redirect to chat
            router.push("/chat");
        } catch (err: any) {
            // Handle different error types
            let errorMessage = "Something went wrong";
            if (err.message === "Failed to fetch") {
                errorMessage = "Cannot connect to server. Make sure backend is running.";
            } else if (typeof err.message === "string") {
                errorMessage = err.message;
            } else if (typeof err === "object" && err.detail) {
                errorMessage = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
            }
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className={styles.main}>
            {/* Background */}
            <div className={styles.bgGradient}></div>
            <div className={styles.bgOrbs}>
                <div className={styles.orb1}></div>
                <div className={styles.orb2}></div>
            </div>

            {/* Back to Home */}
            <button className={styles.backBtn} onClick={() => router.push("/")}>
                ← Back to Home
            </button>

            {/* Auth Card */}
            <div className={styles.authContainer}>
                <div className={styles.authCard}>
                    {/* Logo */}
                    <div className={styles.logo}>
                        <span className={styles.logoIcon}>🧠</span>
                        <span className={styles.logoText}>Research Agent</span>
                    </div>

                    {/* Title */}
                    <h1 className={styles.title}>
                        {isLogin ? "Welcome Back" : "Create Account"}
                    </h1>
                    <p className={styles.subtitle}>
                        {isLogin
                            ? "Sign in to continue your research"
                            : "Start your research journey today"}
                    </p>

                    {/* Toggle */}
                    <div className={styles.toggle}>
                        <button
                            className={`${styles.toggleBtn} ${isLogin ? styles.active : ""}`}
                            onClick={() => setIsLogin(true)}
                        >
                            Login
                        </button>
                        <button
                            className={`${styles.toggleBtn} ${!isLogin ? styles.active : ""}`}
                            onClick={() => setIsLogin(false)}
                        >
                            Sign Up
                        </button>
                    </div>

                    {/* Error */}
                    {error && <div className={styles.error}>{error}</div>}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className={styles.form}>
                        {!isLogin && (
                            <div className={styles.inputGroup}>
                                <label htmlFor="name">Name</label>
                                <input
                                    type="text"
                                    id="name"
                                    name="name"
                                    className="input"
                                    placeholder="Your name"
                                    value={formData.name}
                                    onChange={handleChange}
                                />
                            </div>
                        )}

                        <div className={styles.inputGroup}>
                            <label htmlFor="email">Email</label>
                            <input
                                type="email"
                                id="email"
                                name="email"
                                className="input"
                                placeholder="you@example.com"
                                value={formData.email}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className={styles.inputGroup}>
                            <label htmlFor="password">Password</label>
                            <input
                                type="password"
                                id="password"
                                name="password"
                                className="input"
                                placeholder="••••••••"
                                value={formData.password}
                                onChange={handleChange}
                                required
                                minLength={6}
                            />
                        </div>

                        <button
                            type="submit"
                            className={`btn btn-primary ${styles.submitBtn}`}
                            disabled={loading}
                        >
                            {loading ? (
                                <span className="spinner"></span>
                            ) : isLogin ? (
                                "Sign In"
                            ) : (
                                "Create Account"
                            )}
                        </button>
                    </form>

                    {/* Footer */}
                    <p className={styles.footerText}>
                        {isLogin ? "Don't have an account? " : "Already have an account? "}
                        <button
                            className={styles.linkBtn}
                            onClick={() => setIsLogin(!isLogin)}
                        >
                            {isLogin ? "Sign Up" : "Sign In"}
                        </button>
                    </p>
                </div>
            </div>
        </main>
    );
}
