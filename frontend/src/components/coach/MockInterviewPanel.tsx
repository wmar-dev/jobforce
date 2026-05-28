"use client";

import { useState } from "react";
import { submitAnswer, getSessionSummary } from "@/lib/api";
import type { QuestionItem, AnswerFeedback, SessionSummary } from "@/lib/types";
import { QuestionCard } from "./QuestionCard";

interface MockInterviewPanelProps {
  sessionId: number;
  questions: QuestionItem[];
}

interface AnswerState {
  text: string;
  feedback: AnswerFeedback | null;
  isSubmitting: boolean;
}

export function MockInterviewPanel({ sessionId, questions }: MockInterviewPanelProps) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, AnswerState>>({});
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);

  const currentQuestion = questions[currentIdx];
  const answerState = answers[currentQuestion?.id] ?? {
    text: "",
    feedback: null,
    isSubmitting: false,
  };

  const updateAnswer = (id: string, updates: Partial<AnswerState>) => {
    setAnswers((prev) => {
      const existing = prev[id] ?? { text: "", feedback: null, isSubmitting: false };
      return { ...prev, [id]: { ...existing, ...updates } };
    });
  };

  const handleSubmit = async () => {
    if (!currentQuestion || !answerState.text.trim()) return;
    updateAnswer(currentQuestion.id, { isSubmitting: true });
    try {
      const feedback = await submitAnswer(sessionId, currentQuestion.id, answerState.text);
      updateAnswer(currentQuestion.id, { feedback, isSubmitting: false });
    } catch (err) {
      updateAnswer(currentQuestion.id, { isSubmitting: false });
    }
  };

  const handleFinish = async () => {
    setIsSummaryLoading(true);
    try {
      const s = await getSessionSummary(sessionId);
      setSummary(s);
    } finally {
      setIsSummaryLoading(false);
    }
  };

  if (summary) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <div className="text-center mb-4">
          <div className="text-4xl mb-2">🎯</div>
          <h2 className="text-lg font-bold text-white">Session Complete</h2>
          <div className="text-3xl font-mono font-bold text-blue-400 mt-2">
            {Math.round(summary.overall_score * 100)}%
          </div>
        </div>
        <p className="text-gray-300 text-sm text-center mb-4">{summary.summary}</p>
        {summary.areas_to_improve.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Areas to Improve
            </h3>
            <ul className="space-y-1">
              {summary.areas_to_improve.map((area, i) => (
                <li key={i} className="text-sm text-gray-400 flex items-center gap-2">
                  <span className="text-blue-500">→</span> {area}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  if (!currentQuestion) return null;

  const isLast = currentIdx === questions.length - 1;
  const answeredCount = Object.values(answers).filter((a) => a.feedback !== null).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>
          Question {currentIdx + 1} of {questions.length}
        </span>
        <span>{answeredCount} answered</span>
      </div>

      <QuestionCard question={currentQuestion} />

      <div>
        <textarea
          value={answerState.text}
          onChange={(e) => updateAnswer(currentQuestion.id, { text: e.target.value })}
          placeholder="Type your answer here..."
          rows={5}
          className="w-full px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 placeholder-gray-600 focus:outline-none focus:border-blue-500 resize-none"
        />
      </div>

      {answerState.feedback && (
        <div className="bg-blue-950 border border-blue-900 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-blue-400 uppercase">Coach Feedback</span>
            <span className="text-blue-300 font-mono">
              {Math.round(answerState.feedback.score * 100)}%
            </span>
          </div>
          <p className="text-gray-300 text-sm">{answerState.feedback.feedback}</p>
        </div>
      )}

      <div className="flex gap-2">
        {!answerState.feedback ? (
          <button
            onClick={handleSubmit}
            disabled={answerState.isSubmitting || !answerState.text.trim()}
            className="px-4 py-2 text-sm bg-blue-700 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors"
          >
            {answerState.isSubmitting ? "Submitting..." : "Submit Answer"}
          </button>
        ) : (
          <>
            {!isLast && (
              <button
                onClick={() => setCurrentIdx((i) => i + 1)}
                className="px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
              >
                Next Question →
              </button>
            )}
            {isLast && (
              <button
                onClick={handleFinish}
                disabled={isSummaryLoading}
                className="px-4 py-2 text-sm bg-blue-700 hover:bg-blue-600 disabled:opacity-50 text-white rounded transition-colors"
              >
                {isSummaryLoading ? "Getting Summary..." : "Finish & Get Summary"}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
