import Header from "@/components/layout/Header";

const PIPELINE_FLOW = [
  {
    icon: "🎤",
    title: "Voice Input",
    description: "Browser microphone capture (WebM/Opus)",
    status: "foundation",
  },
  {
    icon: "🗣️",
    title: "Speech-to-Text",
    description: "Sarvam AI (primary, Indic-language) or ElevenLabs",
    status: "interface",
  },
  {
    icon: "🔍",
    title: "Query Processing",
    description: "Language detection, query analysis and expansion",
    status: "interface",
  },
  {
    icon: "📊",
    title: "Adaptive Retrieval",
    description:
      "Dense / Lexical (BM25) / Hybrid retrieval with adaptive routing",
    status: "interface",
  },
  {
    icon: "📈",
    title: "Reranking",
    description: "Cross-encoder reranking of initial candidates",
    status: "interface",
  },
  {
    icon: "🛡️",
    title: "Guardrails",
    description:
      "Input validation, relevance check, confidence threshold, grounding verification",
    status: "interface",
  },
  {
    icon: "✅",
    title: "Grounded Response",
    description:
      "LLM-generated answer verified against retrieved evidence, with abstention support",
    status: "interface",
  },
];

const DIFFERENTIATORS = [
  {
    title: "Voice-First",
    description: "Designed for voice interaction from day one",
  },
  {
    title: "Multilingual / Indic",
    description: "MSMARCO-XI dataset with Indic language coverage via AI4Bharat",
  },
  {
    title: "Multi-Strategy Chunking",
    description:
      "Whole-passage, semantic, sliding window, and metadata-aware strategies",
  },
  {
    title: "Adaptive Retrieval",
    description:
      "Query-aware routing between dense, lexical, and hybrid strategies",
  },
  {
    title: "Structured Orchestration",
    description:
      "Full state machine with retries, fallback, and graceful abstention",
  },
  {
    title: "Real Benchmarks",
    description: "Actual latency measurements — P50, P70, P100 — never faked",
  },
];

type StatusType = "foundation" | "interface" | "planned";

function StatusBadge({ status }: { status: StatusType }) {
  const config = {
    foundation: {
      label: "Foundation Built",
      color: "bg-success/10 text-success border-success/20",
    },
    interface: {
      label: "Interface Ready",
      color: "bg-accent/10 text-accent border-accent/20",
    },
    planned: {
      label: "Planned",
      color: "bg-text-muted/10 text-text-muted border-text-muted/20",
    },
  };
  const c = config[status];
  return (
    <span
      className={`text-[9px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full border ${c.color}`}
    >
      {c.label}
    </span>
  );
}

export default function ArchitecturePage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 max-w-4xl w-full mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-10 animate-fade-in">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            Architecture
          </h1>
          <p className="text-sm text-text-muted mt-1">
            SAMVAD pipeline design and system architecture
          </p>
        </div>

        {/* Pipeline Flow */}
        <section className="mb-12 animate-slide-up">
          <h2 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-[0.2em] mb-6">
            Pipeline Flow
          </h2>
          <div className="space-y-1">
            {PIPELINE_FLOW.map((stage, i) => (
              <div key={stage.title}>
                <div className="flex items-start gap-4 rounded-xl border border-border-subtle bg-bg-surface/50 p-5 hover:border-border-default transition-colors">
                  <div className="w-10 h-10 rounded-lg bg-bg-elevated border border-border-default flex items-center justify-center flex-shrink-0 text-lg">
                    {stage.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="text-sm font-semibold text-text-primary">
                        {stage.title}
                      </h3>
                      <StatusBadge status={stage.status as StatusType} />
                    </div>
                    <p className="text-xs text-text-secondary leading-relaxed">
                      {stage.description}
                    </p>
                  </div>
                </div>
                {i < PIPELINE_FLOW.length - 1 && (
                  <div className="flex justify-start ml-9">
                    <div className="w-px h-4 bg-border-subtle" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Differentiators */}
        <section className="mb-12 animate-slide-up" style={{ animationDelay: "0.1s" }}>
          <h2 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-[0.2em] mb-6">
            Key Differentiators
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {DIFFERENTIATORS.map((d) => (
              <div
                key={d.title}
                className="rounded-xl border border-border-subtle bg-bg-surface/50 p-5"
              >
                <h3 className="text-sm font-semibold text-text-primary mb-1">
                  {d.title}
                </h3>
                <p className="text-xs text-text-secondary leading-relaxed">
                  {d.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Offline vs Online */}
        <section className="mb-12 animate-slide-up" style={{ animationDelay: "0.2s" }}>
          <h2 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-[0.2em] mb-6">
            Offline vs Online Processing
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-xl border border-border-subtle bg-bg-surface/50 p-5">
              <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent" />
                Offline (Pre-computed)
              </h3>
              <ul className="space-y-2 text-xs text-text-secondary">
                <li>• Dataset download and inspection</li>
                <li>• Multi-strategy chunking</li>
                <li>• Embedding generation</li>
                <li>• Vector index creation</li>
                <li>• BM25 index building</li>
                <li>• Persistent storage</li>
              </ul>
            </div>
            <div className="rounded-xl border border-border-subtle bg-bg-surface/50 p-5">
              <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-success" />
                Online (Per-request)
              </h3>
              <ul className="space-y-2 text-xs text-text-secondary">
                <li>• Voice input capture</li>
                <li>• Speech-to-text</li>
                <li>• Query embedding</li>
                <li>• Adaptive retrieval</li>
                <li>• Reranking</li>
                <li>• Guardrails + Generation</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Implementation Status */}
        <section className="animate-slide-up" style={{ animationDelay: "0.3s" }}>
          <h2 className="text-xs font-mono font-semibold text-text-muted uppercase tracking-[0.2em] mb-6">
            Implementation Status
          </h2>
          <div className="rounded-xl border border-border-subtle bg-bg-surface/50 p-6 space-y-4">
            <StatusGroup
              title="Foundation ✓"
              items={[
                { label: "Frontend foundation (Next.js + TypeScript)", done: true },
                { label: "Backend foundation (FastAPI + Pydantic)", done: true },
                { label: "API contracts and schemas", done: true },
                { label: "Pipeline state architecture", done: true },
                { label: "Service interfaces and protocols", done: true },
                { label: "Configuration system", done: true },
                { label: "Error handling and logging", done: true },
                { label: "Analytics framework", done: true },
                { label: "Voice recording infrastructure", done: true },
              ]}
            />
            <div className="border-t border-border-subtle" />
            <StatusGroup
              title="Core AI Pipeline"
              items={[
                { label: "MSMARCO-XI dataset ingestion", done: false },
                { label: "Multi-strategy chunking", done: false },
                { label: "Embedding generation", done: false },
                { label: "Vector index (FAISS/Qdrant)", done: false },
                { label: "Dense retrieval", done: false },
                { label: "Lexical retrieval (BM25)", done: false },
                { label: "Hybrid retrieval and fusion", done: false },
                { label: "Adaptive query routing", done: false },
                { label: "Cross-encoder reranking", done: false },
                { label: "LLM-based generation", done: false },
                { label: "Guardrail implementation", done: false },
                { label: "Real latency benchmarks", done: false },
              ]}
            />
          </div>
        </section>
      </main>
    </div>
  );
}

function StatusGroup({
  title,
  items,
}: {
  title: string;
  items: { label: string; done: boolean }[];
}) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-text-primary mb-3">{title}</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5">
        {items.map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <span
              className={`text-xs ${
                item.done ? "text-success" : "text-text-muted"
              }`}
            >
              {item.done ? "✓" : "□"}
            </span>
            <span
              className={`text-xs ${
                item.done ? "text-text-primary" : "text-text-muted"
              }`}
            >
              {item.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
