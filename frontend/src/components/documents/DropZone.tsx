"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, AlertCircle, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { api, ApiError } from "@/lib/api";
import type { DocumentInfo } from "@/types";

interface DropZoneProps {
  onDocumentUploaded: (document: DocumentInfo) => void;
}

type UploadStatus = "idle" | "uploading" | "success" | "error";

const ACCEPTED_TYPES = [".pdf", ".txt"];

export function DropZone({ onDocumentUploaded }: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const validateFile = (file: File): string | null => {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext)) {
      return `Invalid file type. Accepted: ${ACCEPTED_TYPES.join(", ")}`;
    }
    if (file.size > 10 * 1024 * 1024) {
      return "File too large. Maximum size: 10 MB";
    }
    return null;
  };

  const uploadFile = async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setStatus("error");
      setError(validationError);
      return;
    }

    setStatus("uploading");
    setError(null);
    setUploadedFile(file.name);

    try {
      const response = await api.documents.upload(file);
      setStatus("success");
      onDocumentUploaded(response.document);

      // Reset after success
      setTimeout(() => {
        setStatus("idle");
        setUploadedFile(null);
      }, 2000);
    } catch (err) {
      setStatus("error");
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to upload document");
      }
    }
  };

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        await uploadFile(files[0]);
      }
    },
    [onDocumentUploaded]
  );

  const handleFileInput = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        await uploadFile(files[0]);
      }
      e.target.value = "";
    },
    [onDocumentUploaded]
  );

  return (
    <div
      className={cn(
        "relative rounded-xl border-2 border-dashed transition-all duration-200",
        isDragging && "drop-zone-active",
        status === "idle" && "border-border hover:border-muted-foreground/50",
        status === "uploading" && "border-primary/50 bg-primary/5",
        status === "success" && "border-green-500/50 bg-green-500/5",
        status === "error" && "border-destructive/50 bg-destructive/5"
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept={ACCEPTED_TYPES.join(",")}
        onChange={handleFileInput}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        disabled={status === "uploading"}
      />

      <div className="flex flex-col items-center justify-center p-6 text-center">
        {status === "idle" && (
          <>
            <div className="p-3 rounded-full bg-secondary mb-3">
              <Upload className="w-6 h-6 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-foreground mb-1">
              Drop your document here
            </p>
            <p className="text-xs text-muted-foreground">
              PDF or TXT, up to 10 MB
            </p>
          </>
        )}

        {status === "uploading" && (
          <>
            <div className="p-3 rounded-full bg-primary/10 mb-3">
              <FileText className="w-6 h-6 text-primary animate-pulse" />
            </div>
            <p className="text-sm font-medium text-foreground mb-1">
              Processing document...
            </p>
            <p className="text-xs text-muted-foreground">{uploadedFile}</p>
          </>
        )}

        {status === "success" && (
          <>
            <div className="p-3 rounded-full bg-green-500/10 mb-3">
              <CheckCircle2 className="w-6 h-6 text-green-500" />
            </div>
            <p className="text-sm font-medium text-green-500 mb-1">
              Document uploaded!
            </p>
            <p className="text-xs text-muted-foreground">{uploadedFile}</p>
          </>
        )}

        {status === "error" && (
          <>
            <div className="p-3 rounded-full bg-destructive/10 mb-3">
              <AlertCircle className="w-6 h-6 text-destructive" />
            </div>
            <p className="text-sm font-medium text-destructive mb-1">
              Upload failed
            </p>
            <p className="text-xs text-muted-foreground">{error}</p>
          </>
        )}
      </div>
    </div>
  );
}
