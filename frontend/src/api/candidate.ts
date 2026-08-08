import type { Candidate } from '../types/candidate'

export const SAMPLE_CANDIDATE: Candidate = {
  member: {
    id: 'CAND-001',
    name: 'Sarah Johnson',
    jobRole: 'Senior Data Engineer',
    yearsExperience: 9,
    education: 'MS Computer Science',
    status: 'COMPLETED',
  },
  missions: [
    { day: 7, title: 'Embeddings Explained', passed: true, skipped: null, attempts: 1 },
    { day: 8, title: 'Vector Databases Overview', passed: true, skipped: null, attempts: 1 },
    { day: 10, title: 'Retrieval & Matching Engine', passed: true, skipped: null, attempts: 2 },
    { day: 12, title: 'Prompt Engineering Fundamentals', passed: true, skipped: null, attempts: 4 },
    { day: 16, title: 'Chatbot Backend & API Integration', passed: true, skipped: null, attempts: 1 },
    { day: 22, title: 'Multi-Agent Orchestration', passed: true, skipped: null, attempts: 2 },
    { day: 23, title: 'Model Context Protocol (MCP)', passed: true, skipped: null, attempts: 2 },
    { day: 28, title: 'Docker & Kubernetes Deployment', passed: true, skipped: null, attempts: 3 },
    { day: 29, title: 'Monitoring, Logging & Observability', passed: null, skipped: true, attempts: null },
    { day: 31, title: 'Capstone Project & Final Demo', passed: true, skipped: null, attempts: 1 },
  ],
  signals: { commitDays: 28, missionsCompleted: 30, missionsFirstTry: 20 },
}
