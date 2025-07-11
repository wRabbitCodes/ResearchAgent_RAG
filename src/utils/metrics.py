from prometheus_client import Counter, Histogram

# Count total questions asked
questions_total = Counter("questions_total", "Total number of questions received")

# Count failed LLM responses
llm_failures_total = Counter("llm_failures_total", "Total LLM failures")

# Latency of question answering (seconds)
latency_seconds = Histogram("answer_latency_seconds", "Latency for answering questions")
