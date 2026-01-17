"use client";

import { useState } from "react";
import { User, Sparkles, FileText, ChevronDown } from "lucide-react";
import ReactMarkdown from "react-markdown";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ChatMessage, SourceChunk } from "@/types";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const hasSources = message.sources && message.sources.length > 0;

  return (
    <div
      className={cn(
        "flex gap-3 animate-fade-in",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-primary/20" : "bg-secondary"
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-primary" />
        ) : (
          <Sparkles className="w-4 h-4 text-mistral-orange" />
        )}
      </div>

      {/* Content */}
      <div
        className={cn(
          "flex flex-col max-w-[80%]",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-3",
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-md"
              : "bg-secondary rounded-tl-md"
          )}
        >
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">
              {message.content || "..."}
            </p>
          ) : (
            <div
              className={cn(
                "prose prose-sm dark:prose-invert max-w-none",
                "prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0",
                "prose-headings:my-2 prose-headings:font-semibold",
                "prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs",
                "prose-pre:bg-muted prose-pre:p-3 prose-pre:rounded-lg",
                message.isStreaming && "typing-cursor"
              )}
            >
              <ReactMarkdown>
                {message.content || (message.isStreaming ? "" : "...")}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Sources */}
        {!isUser && hasSources && (
          <div className="w-full mt-2">
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="sources" className="border-none">
                <AccordionTrigger className="py-2 px-3 rounded-lg bg-secondary/50 hover:bg-secondary hover:no-underline">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <FileText className="w-3.5 h-3.5" />
                    <span>
                      Based on {message.sources!.length} document excerpt
                      {message.sources!.length > 1 ? "s" : ""}
                    </span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pt-2">
                  <div className="space-y-2">
                    {message.sources!.map((source, index) => (
                      <SourceCard
                        key={`${source.document_id}-${source.chunk_index}`}
                        source={source}
                        index={index}
                      />
                    ))}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>
        )}
      </div>
    </div>
  );
}

function SourceCard({
  source,
  index,
}: {
  source: SourceChunk;
  index: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const content = source.content;
  const isLong = content.length > 200;
  const displayContent = expanded || !isLong ? content : content.slice(0, 200);

  return (
    <div className="rounded-lg border bg-card p-3 source-highlight">
      <div className="flex items-center gap-2 mb-2">
        <Badge variant="secondary" className="text-[10px]">
          Excerpt {index + 1}
        </Badge>
        <span className="text-[10px] text-muted-foreground">
          {source.document_name}
        </span>
        <span className="text-[10px] text-muted-foreground ml-auto">
          {Math.round(source.score * 100)}% match
        </span>
      </div>
      <p className="text-xs text-muted-foreground leading-relaxed">
        {displayContent}
        {isLong && !expanded && "..."}
      </p>
      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[10px] text-primary hover:underline mt-1"
        >
          {expanded ? "Show less" : "Show more"}
        </button>
      )}
    </div>
  );
}
