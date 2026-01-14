"use client";

import { useState, useCallback } from "react";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { api } from "@/lib/api";
import type { ChatMessage, SourceChunk } from "@/types";

interface ChatInterfaceProps {
  hasDocuments: boolean;
}

export function ChatInterface({ hasDocuments }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = useCallback(async (content: string) => {
    // Add user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
    };
    setMessages((prev) => [...prev, userMessage]);

    // Add placeholder assistant message
    const assistantId = `assistant-${Date.now()}`;
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      isStreaming: true,
    };
    setMessages((prev) => [...prev, assistantMessage]);
    setIsLoading(true);

    try {
      // Build history for context (excluding current messages)
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      let fullContent = "";
      let sources: SourceChunk[] = [];

      // Stream the response
      for await (const event of api.chat.stream(content, history)) {
        if (event.type === "sources") {
          sources = event.data as SourceChunk[];
          // Update immediately with sources
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, sources }
                : m
            )
          );
        } else if (event.type === "content") {
          fullContent += event.data as string;
          // Use flushSync to force immediate render for each chunk
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: fullContent, sources }
                : m
            )
          );
        } else if (event.type === "done") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, isStreaming: false, sources }
                : m
            )
          );
        } else if (event.type === "error") {
          throw new Error(event.data as string);
        }
      }
    } catch (error) {
      // Update with error message
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content:
                  "Sorry, I encountered an error while processing your request. Please try again.",
                isStreaming: false,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <MessageList messages={messages} />
      <div className="p-4 border-t border-border">
        <ChatInput
          onSend={handleSend}
          disabled={!hasDocuments}
          isLoading={isLoading}
          placeholder={
            hasDocuments
              ? "Ask a question about your documents..."
              : "Upload a document first to start chatting"
          }
        />
      </div>
    </div>
  );
}
