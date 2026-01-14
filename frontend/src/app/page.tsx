"use client";

import { useState, useEffect, useCallback } from "react";
import { Sparkles, Github, ExternalLink } from "lucide-react";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { DropZone } from "@/components/documents/DropZone";
import { DocumentList } from "@/components/documents/DocumentList";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { DocumentInfo } from "@/types";

export default function Home() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);

  // Load documents on mount
  useEffect(() => {
    async function loadDocuments() {
      try {
        const response = await api.documents.list();
        setDocuments(response.documents);
      } catch (error) {
        console.error("Failed to load documents:", error);
      } finally {
        setIsLoadingDocs(false);
      }
    }
    loadDocuments();
  }, []);

  const handleDocumentUploaded = useCallback((document: DocumentInfo) => {
    setDocuments((prev) => [document, ...prev.filter((d) => d.id !== document.id)]);
  }, []);

  const handleDeleteDocument = useCallback(async (docId: string) => {
    try {
      await api.documents.delete(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (error) {
      console.error("Failed to delete document:", error);
    }
  }, []);

  return (
    <div className="min-h-screen bg-pattern">
      {/* Header */}
      <header className="border-b border-border bg-background/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-mistral-orange to-mistral-orange-dark">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-foreground">
                  Mistral RAG
                </h1>
                <p className="text-xs text-muted-foreground">
                  Document Q&A powered by Mistral AI
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" asChild>
                <a
                  href="https://docs.mistral.ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-muted-foreground"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span className="hidden sm:inline">Docs</span>
                </a>
              </Button>
              <Button variant="ghost" size="sm" asChild>
                <a
                  href="https://github.com/RicardoBOKA/mistralAI-project-role-application"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-muted-foreground"
                >
                  <Github className="w-4 h-4" />
                  <span className="hidden sm:inline">GitHub</span>
                </a>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6 h-[calc(100vh-8rem)]">
          {/* Sidebar - Documents */}
          <aside className="flex flex-col gap-4 lg:border-r lg:border-border lg:pr-6">
            <div>
              <h2 className="text-sm font-medium text-foreground mb-3">
                Upload Document
              </h2>
              <DropZone onDocumentUploaded={handleDocumentUploaded} />
            </div>

            <div className="flex-1 overflow-hidden">
              <h2 className="text-sm font-medium text-foreground mb-3">
                Your Documents
                {documents.length > 0 && (
                  <span className="ml-2 text-xs text-muted-foreground font-normal">
                    ({documents.length})
                  </span>
                )}
              </h2>
              <div className="h-full overflow-auto pr-2">
                <DocumentList
                  documents={documents}
                  onDelete={handleDeleteDocument}
                  isLoading={isLoadingDocs}
                />
              </div>
            </div>
          </aside>

          {/* Main - Chat */}
          <section className="flex flex-col bg-card rounded-xl border overflow-hidden">
            <div className="px-4 py-3 border-b border-border bg-secondary/30">
              <h2 className="text-sm font-medium text-foreground">
                Chat with your documents
              </h2>
              <p className="text-xs text-muted-foreground">
                Ask questions and get AI-powered answers based on your uploaded
                documents
              </p>
            </div>
            <ChatInterface hasDocuments={documents.length > 0} />
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-xs text-center text-muted-foreground">
            Built with{" "}
            <span className="text-mistral-orange font-medium">Mistral AI</span>,
            Next.js, and FastAPI •{" "}
            <a href="#" className="hover:text-foreground transition-colors">
              View on GitHub
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
