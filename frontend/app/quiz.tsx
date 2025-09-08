import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { CheckCircle, XCircle } from "lucide-react";

const quizQuestions = [
  {
    question:
      "What is the recommended way to handle sensitive user data in Gumloop?",
    options: [
      "Store it directly in local storage for quick access",
      "Encrypt all sensitive data and use secure transmission protocols",
      "Keep it in plain text format for easy debugging",
      "Share it across all user sessions for convenience",
    ],
    correctAnswer: 1,
    explanation:
      "Always encrypt sensitive data and use secure protocols like HTTPS for transmission to protect user information.",
  },
  {
    question:
      "Which practice should be followed when implementing API authentication in Gumloop?",
    options: [
      "Use API keys directly in frontend code",
      "Store authentication tokens in URL parameters",
      "Implement JWT tokens with proper expiration and refresh mechanisms",
      "Share authentication credentials between users",
    ],
    correctAnswer: 2,
    explanation:
      "JWT tokens with proper expiration and refresh mechanisms provide secure authentication while maintaining user sessions safely.",
  },
  {
    question:
      "How should you handle error messages in Gumloop to maintain security?",
    options: [
      "Display detailed error stack traces to users",
      "Show generic error messages to users while logging details securely",
      "Ignore all errors to prevent security breaches",
      "Send all error details to the client console",
    ],
    correctAnswer: 1,
    explanation:
      "Generic error messages prevent exposing sensitive system information while maintaining proper error tracking internally.",
  },
  {
    question:
      "What is the best practice for managing user permissions in Gumloop?",
    options: [
      "Give all users admin access for simplicity",
      "Implement role-based access control (RBAC) with principle of least privilege",
      "Store permissions in client-side cookies",
      "Allow users to modify their own permission levels",
    ],
    correctAnswer: 1,
    explanation:
      "RBAC with least privilege ensures users only have access to the resources they need for their role.",
  },
  {
    question:
      "Which approach should be used for handling file uploads in Gumloop?",
    options: [
      "Accept all file types without validation",
      "Store files directly in the database as raw data",
      "Validate file types, scan for malware, and store in secure cloud storage",
      "Allow unlimited file sizes for user convenience",
    ],
    correctAnswer: 2,
    explanation:
      "Proper file validation, malware scanning, and secure storage prevent security vulnerabilities and ensure safe file handling.",
  },
];

export default function Quiz() {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [score, setScore] = useState(0);
  const [quizCompleted, setQuizCompleted] = useState(false);

  const handleAnswerSelect = (answerIndex: number) => {
    setSelectedAnswer(answerIndex);
    setShowExplanation(true);

    if (answerIndex === quizQuestions[currentQuestion].correctAnswer) {
      setScore(score + 1);
    }
  };

  const handleNextQuestion = () => {
    if (currentQuestion < quizQuestions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
      setSelectedAnswer(null);
      setShowExplanation(false);
    } else {
      setQuizCompleted(true);
    }
  };

  const progress = ((currentQuestion + 1) / quizQuestions.length) * 100;

  if (quizCompleted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="w-full max-w-2xl p-8 space-y-6">
          <h2 className="text-2xl font-bold text-center">Quiz Completed!</h2>
          <div className="text-center">
            <p className="text-xl mb-4">
              Your Score: {score}/{quizQuestions.length}
            </p>
            <p className="text-gray-600">
              {score === quizQuestions.length
                ? "Perfect score! You're well-versed in Gumloop security practices!"
                : "Review the questions you missed to better understand Gumloop security best practices."}
            </p>
          </div>
          <Button
            onClick={() => window.location.reload()}
            className="w-full bg-black hover:bg-gray-900"
          >
            Retake Quiz
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-2xl p-8 space-y-6">
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">
              Question {currentQuestion + 1}/{quizQuestions.length}
            </span>
            <span className="text-sm font-medium">
              Score: {score}/{quizQuestions.length}
            </span>
          </div>
          <Progress value={progress} className="w-full h-2" />
        </div>

        <div className="space-y-4">
          <h3 className="text-xl font-semibold">
            {quizQuestions[currentQuestion].question}
          </h3>
          <div className="space-y-3">
            {quizQuestions[currentQuestion].options.map((option, index) => (
              <Button
                key={index}
                onClick={() => handleAnswerSelect(index)}
                className={`w-full justify-start text-left p-4 h-auto ${
                  selectedAnswer === null
                    ? "hover:bg-gray-100 hover:text-gray-900"
                    : index === quizQuestions[currentQuestion].correctAnswer
                    ? "bg-green-100 hover:bg-green-100 text-gray-900"
                    : selectedAnswer === index
                    ? "bg-red-100 hover:bg-red-100 text-gray-900"
                    : "hover:bg-gray-100 hover:text-gray-900"
                }`}
                variant="ghost"
                disabled={selectedAnswer !== null}
              >
                <div className="flex items-center gap-2">
                  {selectedAnswer !== null &&
                    index === quizQuestions[currentQuestion].correctAnswer && (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    )}
                  {selectedAnswer === index &&
                    index !== quizQuestions[currentQuestion].correctAnswer && (
                      <XCircle className="h-5 w-5 text-red-500" />
                    )}
                  <span>{option}</span>
                </div>
              </Button>
            ))}
          </div>
        </div>

        {showExplanation && (
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              {quizQuestions[currentQuestion].explanation}
            </p>
          </div>
        )}

        {selectedAnswer !== null && (
          <Button
            onClick={handleNextQuestion}
            className="w-full bg-black hover:bg-gray-900"
          >
            {currentQuestion === quizQuestions.length - 1
              ? "Finish Quiz"
              : "Next Question"}
          </Button>
        )}
      </Card>
    </div>
  );
}
