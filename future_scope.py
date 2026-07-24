# 1. Caching layer (Redis)
# Sit a cache in front of expensive DB reads — user sessions, frequently-hit queries, computed aggregates. Cache-aside pattern (check cache → miss → hit DB → populate cache) is the easiest to bolt onto an existing app. Immediately demonstrates you understand read-heavy vs write-heavy tradeoffs and cache invalidation (the classic "hardest problem in CS" line).

# 2. Load balancing + horizontal scaling
# Even a single Next.js app behind a load balancer (or just deployed across multiple instances on Vercel/Railway/Fly.io) shows you're not designing for "runs on my laptop." Pair this with the idea of stateless servers — no in-memory session storage, everything in Redis/DB — since that's why horizontal scaling works at all.

# 3. Message queues / async processing
# Decouple slow or bursty work (emails, image resizing, report generation, webhook processing) from the request-response cycle using a queue (BullMQ, SQS, Inngest). This introduces you to producer-consumer patterns, at-least-once delivery, retries, and dead-letter queues — all real HLD vocabulary.

# 4. Database read replicas / CQRS-lite
# Route reads to a replica and writes to a primary. Doesn't need to be literal (can just be conceptual in your design doc), but if you want to actually implement it, Postgres read replicas + Prisma's readonly connection config is a realistic weekend project. Shows you understand read/write splitting and eventual consistency tradeoffs.

# 5. Rate limiting / API gateway pattern
# Token bucket or sliding-window rate limiting (Upstash Redis makes this trivial) protects against abuse and demonstrates you think about backpressure — what happens when traffic exceeds capacity, not just the happy path.