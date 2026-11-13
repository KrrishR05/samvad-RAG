"use client";

import React from "react";

interface MarkdownAnswerProps {
  content: string;
  totalSources: number;
  onSelectCitation: (oneBasedIndex: number) => void;
}

interface Block {
  type: "heading" | "bullet-list" | "numbered-list" | "code-block" | "hr" | "paragraph";
  level?: number;
  items?: string[];
  text?: string;
  lang?: string;
}

function parseBlocks(markdown: string): Block[] {
  const lines = markdown.split(/\r?\n/);
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // 1. Skip blank lines
    if (!trimmed) {
      i++;
      continue;
    }

    // 2. Fenced code blocks (```lang ... ```)
    if (trimmed.startsWith("```")) {
      const lang = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) i++;
      blocks.push({
        type: "code-block",
        text: codeLines.join("\n"),
        lang,
      });
      continue;
    }

    // 3. Horizontal dividers (---, ***, ___)
    if (/^(?:---|___|\*\*\*)\s*$/.test(trimmed)) {
      blocks.push({ type: "hr" });
      i++;
      continue;
    }

    // 4. Headings (# to ######)
    const headingMatch = /^(#{1,6})\s+(.+)$/.exec(trimmed);
    if (headingMatch) {
      let headingText = headingMatch[2].trim();
      // Strip redundant outer asterisks if LLM wrapped heading in **...**
      if (headingText.startsWith("**") && headingText.endsWith("**") && headingText.length > 4) {
        headingText = headingText.slice(2, -2).trim();
      }
      blocks.push({
        type: "heading",
        level: headingMatch[1].length,
        text: headingText,
      });
      i++;
      continue;
    }

    // 5. Bullet List items (* or -)
    const bulletMatch = /^[\*\-]\s+(.+)$/.exec(trimmed);
    if (bulletMatch) {
      const items: string[] = [];
      while (i < lines.length) {
        const curTrim = lines[i].trim();
        const m = /^[\*\-]\s+(.+)$/.exec(curTrim);
        if (!m) break;
        items.push(m[1].trim());
        i++;
      }
      blocks.push({
        type: "bullet-list",
        items,
      });
      continue;
    }

    // 6. Numbered List items (1. , 2. )
    const numberedMatch = /^(\d+)\.\s+(.+)$/.exec(trimmed);
    if (numberedMatch) {
      const items: string[] = [];
      while (i < lines.length) {
        const curTrim = lines[i].trim();
        const m = /^(\d+)\.\s+(.+)$/.exec(curTrim);
        if (!m) break;
        items.push(m[2].trim());
        i++;
      }
      blocks.push({
        type: "numbered-list",
        items,
      });
      continue;
    }

    // 7. Regular paragraph
    const paraLines: string[] = [];
    while (i < lines.length) {
      const curLine = lines[i];
      const curTrim = curLine.trim();
      if (!curTrim) break;
      // Stop paragraph when hitting another markdown structure
      if (
        curTrim.startsWith("```") ||
        /^(?:---|___|\*\*\*)\s*$/.test(curTrim) ||
        /^#{1,6}\s+/.test(curTrim) ||
        /^[\*\-]\s+/.test(curTrim) ||
        /^\d+\.\s+/.test(curTrim)
      ) {
        break;
      }
      paraLines.push(curTrim);
      i++;
    }
    if (paraLines.length > 0) {
      blocks.push({
        type: "paragraph",
        text: paraLines.join(" "),
      });
    }
  }

  return blocks;
}

function renderInline(
  text: string,
  totalSources: number,
  onSelectCitation: (idx: number) => void
): React.ReactNode[] {
  // Matches: [1], [1, 2], `inline code`, **bold**, *italic*
  const TOKEN_REGEX = /(\[\d+(?:\s*,\s*\d+)*\]|`[^`]+?`|\*\*[^*]+?\*\*|\*[^*]+?\*)/g;
  const parts = text.split(TOKEN_REGEX);

  return parts.filter(Boolean).map((part, idx) => {
    // Citation pill: [1] or [1, 2, 3]
    if (part.startsWith("[") && part.endsWith("]")) {
      const match = /^\[(\d+(?:\s*,\s*\d+)*)\]$/.exec(part);
      if (match) {
        const nums = match[1]
          .split(",")
          .map((s) => parseInt(s.trim(), 10))
          .filter((n) => !isNaN(n));

        return (
          <span key={idx} className="inline-flex items-center gap-1 mx-0.5 align-baseline">
            {nums.map((citNum, cIdx) => {
              const valid = citNum >= 1 && citNum <= totalSources;
              if (!valid) {
                return (
                  <span
                    key={cIdx}
                    className="inline-flex items-center justify-center px-1.5 py-0 text-[10px] font-mono-tech font-semibold rounded bg-[var(--bg-surface)] text-[var(--text-muted)] border border-[var(--border-subtle)]"
                  >
                    {citNum}
                  </span>
                );
              }
              return (
                <button
                  key={cIdx}
                  type="button"
                  onClick={() => onSelectCitation(citNum)}
                  title={`Inspect source [${citNum}]`}
                  className="inline-flex items-center justify-center px-1.5 py-0 text-[11px] font-mono-tech font-semibold rounded bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-border)] hover:bg-[var(--accent)] hover:text-white transition-all cursor-pointer shadow-xs active:scale-95"
                >
                  {citNum}
                </button>
              );
            })}
          </span>
        );
      }
    }

    // Inline code
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      return (
        <code
          key={idx}
          className="px-1.5 py-0.5 rounded bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--accent)] font-mono text-[13px]"
        >
          {part.slice(1, -1)}
        </code>
      );
    }

    // Bold text
    if (part.startsWith("**") && part.endsWith("**") && part.length >= 4) {
      return (
        <strong key={idx} className="font-semibold text-[var(--text-primary)]">
          {renderInline(part.slice(2, -2), totalSources, onSelectCitation)}
        </strong>
      );
    }

    // Italic text
    if (part.startsWith("*") && part.endsWith("*") && part.length >= 2) {
      return (
        <em key={idx} className="italic text-[var(--text-primary)]">
          {renderInline(part.slice(1, -1), totalSources, onSelectCitation)}
        </em>
      );
    }

    // Plain text
    return <React.Fragment key={idx}>{part}</React.Fragment>;
  });
}

export function MarkdownAnswer({
  content,
  totalSources,
  onSelectCitation,
}: MarkdownAnswerProps) {
  const blocks = parseBlocks(content);

  return (
    <div className="space-y-3 font-sans text-[var(--text-primary)]">
      {blocks.map((block, idx) => {
        if (block.type === "heading") {
          const headingContent = renderInline(
            block.text || "",
            totalSources,
            onSelectCitation
          );

          if (block.level === 1) {
            return (
              <h3
                key={idx}
                className="text-lg font-bold text-[var(--text-primary)] mt-5 mb-2 pb-1.5 border-b border-[var(--border-subtle)]"
              >
                {headingContent}
              </h3>
            );
          }
          if (block.level === 2) {
            return (
              <h4
                key={idx}
                className="text-[16px] font-bold text-[var(--text-primary)] mt-4 mb-2"
              >
                {headingContent}
              </h4>
            );
          }
          if (block.level === 3) {
            return (
              <h5
                key={idx}
                className="text-[15px] font-semibold text-[var(--accent)] mt-3.5 mb-1.5"
              >
                {headingContent}
              </h5>
            );
          }
          return (
            <h6
              key={idx}
              className="text-[13.5px] font-semibold text-[var(--text-secondary)] mt-2.5 mb-1 uppercase tracking-wide font-mono-tech"
            >
              {headingContent}
            </h6>
          );
        }

        if (block.type === "bullet-list" && block.items) {
          return (
            <ul key={idx} className="my-2 space-y-1.5 pl-0.5">
              {block.items.map((item, iIdx) => (
                <li
                  key={iIdx}
                  className="flex items-start gap-2.5 text-[14.5px] leading-relaxed text-[var(--text-primary)]"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] mt-2 shrink-0" />
                  <span className="flex-1">
                    {renderInline(item, totalSources, onSelectCitation)}
                  </span>
                </li>
              ))}
            </ul>
          );
        }

        if (block.type === "numbered-list" && block.items) {
          return (
            <ol key={idx} className="my-2 space-y-1.5 pl-0.5">
              {block.items.map((item, iIdx) => (
                <li
                  key={iIdx}
                  className="flex items-start gap-2.5 text-[14.5px] leading-relaxed text-[var(--text-primary)]"
                >
                  <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[11px] font-mono-tech font-semibold text-[var(--text-secondary)] shrink-0 mt-0.5">
                    {iIdx + 1}
                  </span>
                  <span className="flex-1">
                    {renderInline(item, totalSources, onSelectCitation)}
                  </span>
                </li>
              ))}
            </ol>
          );
        }

        if (block.type === "hr") {
          return <hr key={idx} className="my-3.5 border-[var(--border-subtle)]" />;
        }

        if (block.type === "code-block") {
          return (
            <div
              key={idx}
              className="my-3 rounded-lg overflow-hidden border border-[var(--border-subtle)] bg-[var(--bg-surface)]"
            >
              {block.lang && (
                <div className="px-3 py-1 bg-[var(--bg-panel)] border-b border-[var(--border-subtle)] text-[10px] font-mono-tech uppercase text-[var(--text-muted)]">
                  {block.lang}
                </div>
              )}
              <pre className="p-3 text-[13px] font-mono text-[var(--text-primary)] overflow-x-auto leading-normal">
                <code>{block.text}</code>
              </pre>
            </div>
          );
        }

        // Paragraph
        return (
          <p
            key={idx}
            className="text-[14.5px] leading-[1.75] text-[var(--text-primary)] mb-2.5"
          >
            {renderInline(block.text || "", totalSources, onSelectCitation)}
          </p>
        );
      })}
    </div>
  );
}

