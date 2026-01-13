"use client";

import { FileText, Trash2, FileType } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatFileSize, formatDate } from "@/lib/utils";
import type { DocumentInfo } from "@/types";

interface DocumentListProps {
  documents: DocumentInfo[];
  onDelete: (docId: string) => void;
  isLoading?: boolean;
}

export function DocumentList({
  documents,
  onDelete,
  isLoading,
}: DocumentListProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2].map((i) => (
          <div
            key={i}
            className="flex items-center gap-3 p-3 rounded-lg bg-secondary/50 animate-shimmer"
          >
            <div className="w-8 h-8 rounded-md bg-muted" />
            <div className="flex-1 space-y-1.5">
              <div className="h-4 w-32 rounded bg-muted" />
              <div className="h-3 w-24 rounded bg-muted" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-8">
        <FileType className="w-10 h-10 mx-auto text-muted-foreground/50 mb-3" />
        <p className="text-sm text-muted-foreground">
          No documents uploaded yet
        </p>
        <p className="text-xs text-muted-foreground/70 mt-1">
          Upload a document to start asking questions
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className="group flex items-center gap-3 p-3 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors"
        >
          <div className="flex-shrink-0 p-2 rounded-md bg-primary/10">
            <FileText className="w-4 h-4 text-primary" />
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">
              {doc.filename}
            </p>
            <div className="flex items-center gap-2 mt-0.5">
              <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                {doc.file_type.toUpperCase()}
              </Badge>
              <span className="text-[10px] text-muted-foreground">
                {formatFileSize(doc.file_size)}
              </span>
              <span className="text-[10px] text-muted-foreground">•</span>
              <span className="text-[10px] text-muted-foreground">
                {doc.chunk_count} chunks
              </span>
            </div>
          </div>

          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive"
            onClick={() => onDelete(doc.id)}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      ))}
    </div>
  );
}
