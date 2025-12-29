"use client";

import React from "react";
import styles from "./LoadingSpinner.module.css";

interface LoadingSpinnerProps {
  size?: "small" | "medium" | "large";
  color?: string;
  text?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = "medium",
  color,
  text,
}) => {
  const spinnerClass = `${styles.spinner} ${styles[size]}`;

  return (
    <div className={styles.container}>
      <div
        className={spinnerClass}
        style={color ? { borderTopColor: color } : undefined}
        role="status"
        aria-label="Loading"
      />
      {text && <span className={styles.text}>{text}</span>}
    </div>
  );
};

interface ProgressBarProps {
  progress: number; // 0-100
  showPercentage?: boolean;
  size?: "small" | "medium" | "large";
  color?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  showPercentage = true,
  size = "medium",
  color,
}) => {
  return (
    <div className={`${styles.progressContainer} ${styles[size]}`}>
      <div
        className={styles.progressBar}
        style={{
          width: `${Math.min(100, Math.max(0, progress))}%`,
          backgroundColor: color || "#007bff",
        }}
        role="progressbar"
        aria-valuenow={progress}
        aria-valuemin={0}
        aria-valuemax={100}
      />
      {showPercentage && (
        <span className={styles.progressText}>{Math.round(progress)}%</span>
      )}
    </div>
  );
};

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string;
  variant?: "text" | "circular" | "rectangular";
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = "100%",
  height = 20,
  borderRadius = "4px",
  variant = "text",
}) => {
  const skeletonStyle: React.CSSProperties = {
    width,
    height,
    borderRadius: variant === "circular" ? "50%" : borderRadius,
  };

  return <div className={styles.skeleton} style={skeletonStyle} />;
};

interface SkeletonListProps {
  count?: number;
  itemHeight?: number;
  itemWidth?: string;
}

export const SkeletonList: React.FC<SkeletonListProps> = ({
  count = 3,
  itemHeight = 60,
  itemWidth = "100%",
}) => {
  return (
    <div className={styles.skeletonList}>
      {Array.from({ length: count }).map((_, index) => (
        <Skeleton
          key={index}
          width={itemWidth}
          height={itemHeight}
          borderRadius="8px"
        />
      ))}
    </div>
  );
};

interface SkeletonChatProps {
  showMessages?: boolean;
  showInput?: boolean;
}

export const SkeletonChat: React.FC<SkeletonChatProps> = ({
  showMessages = true,
  showInput = true,
}) => {
  return (
    <div className={styles.skeletonChat}>
      {showMessages && (
        <div className={styles.skeletonMessages}>
          {/* Assistant message */}
          <div className={styles.skeletonMessage}>
            <Skeleton width={40} height={40} variant="circular" />
            <div className={styles.skeletonMessageContent}>
              <Skeleton width="60%" height={16} borderRadius="8px" />
              <Skeleton width="80%" height={16} borderRadius="8px" />
              <Skeleton width="40%" height={16} borderRadius="8px" />
            </div>
          </div>

          {/* User message */}
          <div className={`${styles.skeletonMessage} ${styles.userMessage}`}>
            <div className={styles.skeletonMessageContent}>
              <Skeleton width="70%" height={16} borderRadius="8px" />
              <Skeleton width="50%" height={16} borderRadius="8px" />
            </div>
            <Skeleton width={40} height={40} variant="circular" />
          </div>
        </div>
      )}

      {showInput && (
        <div className={styles.skeletonInput}>
          <Skeleton width="100%" height={50} borderRadius="8px" />
        </div>
      )}
    </div>
  );
};

// File upload progress component
interface FileUploadProgressProps {
  filename: string;
  progress: number;
  speed?: string;
  onCancel?: () => void;
}

export const FileUploadProgress: React.FC<FileUploadProgressProps> = ({
  filename,
  progress,
  speed,
  onCancel,
}) => {
  return (
    <div className={styles.fileUploadProgress}>
      <div className={styles.fileInfo}>
        <span className={styles.fileIcon}>📄</span>
        <span className={styles.fileName}>{filename}</span>
        {onCancel && (
          <button className={styles.cancelBtn} onClick={onCancel}>
            ✕
          </button>
        )}
      </div>
      <ProgressBar progress={progress} size="small" />
      <div className={styles.uploadStats}>
        <span>{Math.round(progress)}%</span>
        {speed && <span className={styles.uploadSpeed}>{speed}</span>}
      </div>
    </div>
  );
};

// PDF download progress component
interface PDFDownloadProgressProps {
  filename: string;
  progress: number;
  pageCount?: number;
  currentPage?: number;
  onCancel?: () => void;
}

export const PDFDownloadProgress: React.FC<PDFDownloadProgressProps> = ({
  filename,
  progress,
  pageCount,
  currentPage,
  onCancel,
}) => {
  return (
    <div className={styles.pdfDownloadProgress}>
      <div className={styles.downloadHeader}>
        <span className={styles.pdfIcon}>📥</span>
        <span className={styles.downloadTitle}>Downloading PDF</span>
        {onCancel && (
          <button className={styles.cancelBtn} onClick={onCancel}>
            ✕
          </button>
        )}
      </div>
      <div className={styles.downloadFileInfo}>
        <span className={styles.fileName}>{filename}</span>
        {pageCount && currentPage && (
          <span className={styles.pageInfo}>
            Page {currentPage} of {pageCount}
          </span>
        )}
      </div>
      <ProgressBar progress={progress} showPercentage />
    </div>
  );
};

export default LoadingSpinner;
