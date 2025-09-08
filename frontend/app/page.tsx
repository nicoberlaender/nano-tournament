"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  OneTimePasswordField,
  OneTimePasswordFieldInput,
} from "@/components/ui/one-time-password-field";

export default function Home() {
  const [sessionCode, setSessionCode] = useState("");
  const [isJoining, setIsJoining] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const router = useRouter();

  const handleJoinSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (sessionCode.length !== 6) return;

    setIsJoining(true);

    // Simulate brief loading
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Navigate to battle session
    router.push(`/battle/${sessionCode.toUpperCase()}`);
  };

  const handleCreateSession = async () => {
    setIsCreating(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Create a new session
      const response = await fetch(`${apiUrl}/session/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      });

      if (response.ok) {
        const data = await response.json();
        // Navigate to the new session
        router.push(`/battle/${data.session_id}`);
      } else {
        throw new Error('Failed to create session');
      }
    } catch (error) {
      console.error('Failed to create session:', error);
      // Fallback: Generate a random session code
      const randomCode = Math.random().toString(36).substring(2, 8).toUpperCase();
      router.push(`/battle/${randomCode}`);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="min-h-screen p-4" style={{ backgroundColor: "#B7B1F2" }}>
      <div className="w-full max-w-lg mx-auto">
        {/* Header */}
        <div className="text-center space-y-8 pt-16 pb-12">
          <div className="text-8xl mb-8">🤖</div>
          <div>
            <h1 className="text-5xl text-black mb-4 font-black">Nano Tournament</h1>
            <p className="text-2xl text-black font-bold">
              Join or create a battle session
            </p>
          </div>
        </div>

        {/* Centered Input and Button */}
        <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-8">
          {/* Create New Session Button */}
          <Button
            onClick={handleCreateSession}
            disabled={isCreating}
            className="w-full text-3xl py-8 rounded-2xl font-black text-black hover:scale-105 transition-all duration-200 border-4 border-black"
            style={{ backgroundColor: "#FBF3B9" }}
          >
            {isCreating ? "Creating..." : "🚀 Create New Battle"}
          </Button>

          {/* Divider */}
          <div className="flex items-center w-full">
            <div className="flex-1 border-t-4 border-black"></div>
            <div className="px-4 text-2xl font-black text-black">OR</div>
            <div className="flex-1 border-t-4 border-black"></div>
          </div>

          {/* Join Existing Session */}
          <form onSubmit={handleJoinSession} className="w-full space-y-8">
            <div className="text-center mb-4">
              <p className="text-xl text-black font-bold">
                Enter 6-digit session code
              </p>
            </div>
            <div className="flex justify-center px-4">
              <OneTimePasswordField
                value={sessionCode}
                onValueChange={(value) => setSessionCode(value.toUpperCase())}
                className="gap-3"
              >
                {Array.from({ length: 6 }, (_, index) => (
                  <OneTimePasswordFieldInput key={index} index={index} />
                ))}
              </OneTimePasswordField>
            </div>
            <Button
              type="submit"
              disabled={sessionCode.length !== 6 || isJoining}
              className="w-full text-3xl py-8 rounded-2xl font-black text-black hover:scale-105 transition-all duration-200 border-4 border-black disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ backgroundColor: "#FDB7EA" }}
            >
              {isJoining ? "Joining..." : "Join Battle"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
