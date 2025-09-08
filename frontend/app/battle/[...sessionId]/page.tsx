"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";

interface Participant {
  id: string;
  name: string;
  joinedAt: Date;
}

interface BattleResults {
  winner_user_id: string;
  battle_script: string;
  battle_summary: string;
}

type GameState = "join" | "lobby" | "prompt" | "waiting" | "battle" | "results";

export default function BattleSession() {
  const params = useParams();
  const sessionId = Array.isArray(params.sessionId)
    ? params.sessionId[0]
    : params.sessionId;

  const [gameState, setGameState] = useState<GameState>("join");
  const [playerName, setPlayerName] = useState("");
  const [currentPlayer, setCurrentPlayer] = useState<Participant | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [isJoining, setIsJoining] = useState(false);
  const [battleStartTimer, setBattleStartTimer] = useState(5);
  const [prompt, setPrompt] = useState("");
  const [isCreatingCharacter, setIsCreatingCharacter] = useState(false);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [waitingTimer, setWaitingTimer] = useState(3);
  const [battleResults, setBattleResults] = useState<BattleResults | null>(
    null
  );
  const [isConnected, setIsConnected] = useState(false);
  const [userId] = useState(
    () => `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  );
  const [realParticipants, setRealParticipants] = useState<string[]>([]);

  // WebSocket connection and event handlers
  useEffect(() => {
    let mounted = true;

    const connectWebSocket = async () => {
      try {
        await api.connect(userId);
        if (mounted) {
          setIsConnected(true);

          // Join the session if we have one
          if (sessionId) {
            api.joinSession(sessionId);
          }
        }
      } catch (error) {
        console.error("Failed to connect WebSocket:", error);
      }
    };

    connectWebSocket();

    return () => {
      mounted = false;
      api.disconnect();
      setIsConnected(false);
    };
  }, [userId, sessionId]);

  // Setup WebSocket event listeners
  useEffect(() => {
    const handleRoundStart = (data: any) => {
      console.log("Round started:", data);
      setGameState("prompt");
    };

    const handleBattleStart = (data: any) => {
      console.log("Battle started:", data);
      setGameState("battle");
    };

    const handleResults = (data: any) => {
      console.log("Battle results:", data);
      setBattleResults({
        winner_user_id: data.winner_user_id,
        battle_script: data.battle_script,
        battle_summary: data.battle_summary,
      });
      setGameState("results");
    };

    const handleUserJoined = (data: any) => {
      console.log("User joined session:", data);
      setRealParticipants((prev) => [
        ...prev.filter((id) => id !== data.user_id),
        data.user_id,
      ]);
    };

    const handleUserLeft = (data: any) => {
      console.log("User left session:", data);
      setRealParticipants((prev) => prev.filter((id) => id !== data.user_id));
    };

    api.on("round_start", handleRoundStart);
    api.on("battle_start", handleBattleStart);
    api.on("results", handleResults);
    api.on("user_joined_session", handleUserJoined);
    api.on("user_left_session", handleUserLeft);

    return () => {
      api.off("round_start", handleRoundStart);
      api.off("battle_start", handleBattleStart);
      api.off("results", handleResults);
      api.off("user_joined_session", handleUserJoined);
      api.off("user_left_session", handleUserLeft);
    };
  }, []);

  // Update participants list with real and mock data
  useEffect(() => {
    if (gameState === "lobby") {
      const mockParticipants: Participant[] = [
        { id: "1", name: "Alex Chen", joinedAt: new Date(Date.now() - 30000) },
        {
          id: "2",
          name: "Maria Garcia",
          joinedAt: new Date(Date.now() - 25000),
        },
      ];

      let allParticipants = [...mockParticipants];
      if (currentPlayer) {
        allParticipants.push(currentPlayer);
      }

      setParticipants(allParticipants);
    }
  }, [gameState, currentPlayer, realParticipants]);

  // Battle start timer
  useEffect(() => {
    if (gameState === "lobby" && battleStartTimer > 0) {
      const timer = setTimeout(() => {
        setBattleStartTimer((prev) => prev - 1);
      }, 1000);

      return () => clearTimeout(timer);
    } else if (gameState === "lobby" && battleStartTimer === 0) {
      setGameState("prompt");
    }
  }, [gameState, battleStartTimer]);

  // Waiting for players timer
  useEffect(() => {
    if (gameState === "waiting" && waitingTimer > 0) {
      const timer = setTimeout(() => {
        setWaitingTimer((prev) => prev - 1);
      }, 1000);

      return () => clearTimeout(timer);
    } else if (gameState === "waiting" && waitingTimer === 0) {
      setGameState("battle");
    }
  }, [gameState, waitingTimer]);

  const handleJoinSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!playerName.trim()) return;

    setIsJoining(true);

    try {
      // Create or join session via REST API
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;

      // First, try to create user
      const userResponse = await fetch(`${apiUrl}/users/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          name: playerName.trim(),
        }),
      });

      // Try to join existing session, or create one if needed
      let sessionResponse;
      try {
        sessionResponse = await fetch(`${apiUrl}/session/${sessionId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId }),
        });
      } catch (error) {
        // Session might not exist, create it
        sessionResponse = await fetch(`${apiUrl}/session/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId }),
        });
      }

      if (sessionResponse.ok) {
        const newPlayer: Participant = {
          id: userId,
          name: playerName.trim(),
          joinedAt: new Date(),
        };

        setCurrentPlayer(newPlayer);
        setGameState("lobby");

        // Join the WebSocket session
        if (isConnected) {
          api.joinSession(sessionId);
        }
      } else {
        throw new Error("Failed to join session");
      }
    } catch (error) {
      console.error("Failed to join session:", error);
      // Fallback to mock behavior
      const newPlayer: Participant = {
        id: userId,
        name: playerName.trim(),
        joinedAt: new Date(),
      };
      setCurrentPlayer(newPlayer);
      setGameState("lobby");
    } finally {
      setIsJoining(false);
    }
  };

  const handleCreateCharacter = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsCreatingCharacter(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const response = await fetch(`${apiUrl}/generate/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: prompt.trim(),
          session_id: sessionId,
          user_id: userId,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setGeneratedImage(`data:image/png;base64,${data.image_base64}`);
        setGameState("waiting");
      } else {
        throw new Error("Failed to generate character");
      }
    } catch (error) {
      console.error("Failed to generate character:", error);
      // Fallback to mock image
      setGeneratedImage(
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'%3E%3Crect width='400' height='400' fill='%23FBF3B9'/%3E%3Ctext x='200' y='200' text-anchor='middle' dominant-baseline='middle' font-size='20' fill='%23000'%3EGenerated Character%3C/text%3E%3C/svg%3E"
      );
      setGameState("waiting");
    } finally {
      setIsCreatingCharacter(false);
    }
  };

  if (gameState === "join") {
    return (
      <div
        className="min-h-screen flex flex-col p-4"
        style={{ backgroundColor: "#B7B1F2" }}
      >
        <div className="w-full max-w-lg mx-auto flex flex-col justify-between min-h-screen p-4">
          <div className="text-center">
            <div className="text-8xl mb-6">🎮</div>
            <h1 className="text-5xl text-black mb-4 font-black">
              What is your name?
            </h1>
            <p className="text-2xl text-black font-bold">
              Session: {sessionId}
            </p>
          </div>

          <form onSubmit={handleJoinSession} className="space-y-8 pb-12">
            <div className="space-y-4">
              <Input
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                placeholder="Enter your name"
                className="text-2xl py-6 border-4 border-black font-bold text-black placeholder:text-gray-600"
                style={{ backgroundColor: "#FBF3B9" }}
                maxLength={20}
                required
              />
            </div>
            <Button
              type="submit"
              disabled={!playerName.trim() || isJoining}
              className="w-full text-2xl py-6 rounded-2xl font-black text-black hover:scale-105 transition-all duration-200 border-4 border-black"
              style={{ backgroundColor: "#FDB7EA" }}
            >
              {isJoining ? "Joining..." : "Enter Arena"}
            </Button>
          </form>
        </div>
      </div>
    );
  }

  if (gameState === "lobby") {
    return (
      <div
        className="min-h-screen flex flex-col p-4"
        style={{ backgroundColor: "#B7B1F2" }}
      >
        <div className="w-full max-w-6xl mx-auto flex flex-col justify-between min-h-screen p-4">
          {/* Header */}
          <div className="text-center">
            <h1 className="text-5xl md:text-7xl font-black text-black mb-4">
              Waiting for Battle to Begin
            </h1>
            <p className="text-3xl text-black font-bold mb-8">
              Session: {sessionId}
            </p>

            {/* Players List */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {participants.map((participant, index) => (
                <div
                  key={participant.id}
                  className="p-4 rounded-2xl border-4 border-black text-center"
                  style={{ backgroundColor: "#FBF3B9" }}
                >
                  <div className="text-xl font-black text-black">
                    {participant.name}
                  </div>
                  {participant.id === currentPlayer?.id && (
                    <div className="text-sm font-bold text-black opacity-75 mt-1">
                      You
                    </div>
                  )}
                  {index === 0 && participant.id !== currentPlayer?.id && (
                    <div className="text-sm font-bold text-black opacity-75 mt-1">
                      Host
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Waiting Message with Timer */}
          <div className="text-center pb-12">
            <div
              className="inline-flex items-center gap-4 px-8 py-4 rounded-2xl border-4 border-black"
              style={{ backgroundColor: "#FDB7EA" }}
            >
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center font-black text-black text-xl border-2 border-black"
                style={{ backgroundColor: "#FBF3B9" }}
              >
                {battleStartTimer}
              </div>
              <span className="text-black font-black text-2xl">
                Battle starting in {battleStartTimer} seconds...
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (gameState === "prompt") {
    return (
      <div
        className="min-h-screen flex flex-col p-4"
        style={{ backgroundColor: "#B7B1F2" }}
      >
        <div className="w-full max-w-2xl mx-auto flex flex-col justify-between min-h-screen p-4">
          {/* Header */}
          <div className="text-center">
            <Badge
              className="text-xl px-4 py-2 font-black border-4 border-black mb-6"
              style={{ backgroundColor: "#FDB7EA", color: "#000" }}
            >
              ✨ Round 1
            </Badge>
            <p className="text-xl text-black font-bold">
              Describe your Fighter!
            </p>

            {/* Image Display Area */}
            <div className="w-full aspect-square max-w-md mx-auto mt-8">
              <div
                className="w-full h-full rounded-3xl border-4 border-black flex items-center justify-center overflow-hidden"
                style={{
                  backgroundColor: generatedImage ? "transparent" : "#FBF3B9",
                }}
              >
                {generatedImage ? (
                  <img
                    src={generatedImage}
                    alt="Generated Character"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-center">
                    <div className="text-6xl mb-4 opacity-50">🖼️</div>
                    <p className="text-black font-bold text-lg opacity-50">
                      Your character will appear here
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Input and Button Area */}
          <form onSubmit={handleCreateCharacter} className="space-y-6 pb-12">
            <div className="space-y-4">
              <label className="text-2xl font-bold text-black block">
                Character Description
              </label>
              <Input
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe your character... (e.g., 'A brave knight with golden armor and a magic sword')"
                className="text-lg p-4 border-4 border-black font-bold text-black placeholder:text-gray-600 min-h-[60px]"
                style={{ backgroundColor: "#FBF3B9" }}
                maxLength={500}
                required
              />
              <div className="text-right">
                <span className="text-sm font-bold text-black opacity-75">
                  {prompt.length}/500
                </span>
              </div>
            </div>

            <Button
              type="submit"
              disabled={!prompt.trim() || isCreatingCharacter}
              className="w-full text-2xl py-6 rounded-2xl font-black text-black hover:scale-105 transition-all duration-200 border-4 border-black"
              style={{ backgroundColor: "#FDB7EA" }}
            >
              {isCreatingCharacter ? (
                <>
                  <div className="w-6 h-6 rounded-full border-4 border-black border-t-transparent animate-spin mr-2"></div>
                  Creating Character...
                </>
              ) : (
                "Create Character"
              )}
            </Button>
          </form>

          {/* Optional: Add regenerate button if character exists */}
          {generatedImage && !isCreatingCharacter && (
            <div className="mt-6">
              <Button
                onClick={() =>
                  handleCreateCharacter(new Event("submit") as any)
                }
                className="w-full text-xl py-4 rounded-2xl font-black text-black hover:scale-105 transition-all duration-200 border-4 border-black"
                style={{ backgroundColor: "#B7B1F2" }}
              >
                Regenerate Character
              </Button>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (gameState === "waiting") {
    return (
      <div
        className="min-h-screen flex flex-col p-4"
        style={{ backgroundColor: "#B7B1F2" }}
      >
        <div className="w-full max-w-2xl mx-auto flex flex-col justify-between min-h-screen p-4">
          {/* Header */}
          <div className="text-center">
            <Badge
              className="text-xl px-4 py-2 font-black border-4 border-black mb-6"
              style={{ backgroundColor: "#FDB7EA", color: "#000" }}
            >
              ✨ Round 1
            </Badge>
            <h1 className="text-4xl md:text-5xl font-black text-black mb-4">
              Character Ready!
            </h1>
            <p className="text-xl text-black font-bold mb-8">
              Waiting for all players to finish...
            </p>

            {/* Display the generated character */}
            <div className="w-full aspect-square max-w-md mx-auto mb-8">
              <div className="w-full h-full rounded-3xl border-4 border-black overflow-hidden">
                {generatedImage && (
                  <img
                    src={generatedImage}
                    alt="Your Character"
                    className="w-full h-full object-cover"
                  />
                )}
              </div>
            </div>

            {/* Character description */}
            <div className="text-center space-y-4">
              <h2 className="text-2xl font-black text-black">Your Character</h2>
              <div
                className="p-4 rounded-2xl border-4 border-black"
                style={{ backgroundColor: "#FBF3B9" }}
              >
                <p className="text-lg font-bold text-black">{prompt}</p>
              </div>
            </div>
          </div>

          {/* Waiting timer */}
          <div className="text-center pb-12">
            <div
              className="inline-flex items-center gap-4 px-8 py-4 rounded-2xl border-4 border-black"
              style={{ backgroundColor: "#B7B1F2" }}
            >
              <div className="text-2xl">⏰</div>
              <span className="text-black font-black text-xl">
                Battle starting in {waitingTimer} seconds...
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (gameState === "battle") {
    return (
      <>
        <style jsx>{`
          @keyframes slide {
            0% {
              transform: translateX(0);
            }
            100% {
              transform: translateX(40px);
            }
          }
        `}</style>
        <div className="min-h-screen" style={{ backgroundColor: "#B7B1F2" }}>
          {/* Battle Header - Player vs Player */}
          <div className="w-full p-6" style={{ backgroundColor: "#B7B1F2" }}>
            <div className="max-w-4xl mx-auto flex items-center justify-between">
              {/* Player 1 */}
              <div className="flex items-center gap-4">
                <div>
                  <div className="text-2xl font-black text-black">
                    {currentPlayer?.name}
                  </div>
                </div>
              </div>

              {/* VS Badge */}
              <Badge
                className="text-3xl px-8 py-4 font-black border-4 border-black"
                style={{ backgroundColor: "#FBF3B9", color: "#000" }}
              >
                VS
              </Badge>

              {/* Player 2 (Opponent) */}
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-2xl font-black text-black">
                    Alex Chen
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Battle Video Area */}
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="w-full max-w-4xl aspect-video">
              <div
                className="w-full h-full rounded-3xl border-4 border-black flex items-center justify-center relative overflow-hidden"
                style={{ backgroundColor: "#000" }}
              >
                {/* Mock video background */}
                <div
                  className="absolute inset-0 opacity-20"
                  style={{
                    background:
                      "linear-gradient(45deg, #FDB7EA 25%, #FBF3B9 25%, #FBF3B9 50%, #FDB7EA 50%, #FDB7EA 75%, #FBF3B9 75%)",
                    backgroundSize: "40px 40px",
                    animation: "slide 2s linear infinite",
                  }}
                />

                {/* Play indicator */}
                <div className="text-center z-10">
                  <div className="text-8xl mb-4">▶️</div>
                  <p className="text-white font-black text-2xl">
                    Battle in Progress
                  </p>
                  <p className="text-white font-bold text-lg opacity-75">
                    Epic showdown between characters!
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Battle Status */}
          <div className="p-6">
            <div className="max-w-4xl mx-auto text-center">
              <Badge
                className="text-xl px-6 py-3 font-black border-4 border-black"
                style={{ backgroundColor: "#FDB7EA", color: "#000" }}
              >
                ✨ Round 1 of 3
              </Badge>
            </div>
          </div>
        </div>
      </>
    );
  }

  if (gameState === "results" && battleResults) {
    return (
      <div
        className="min-h-screen flex flex-col p-4"
        style={{ backgroundColor: "#B7B1F2" }}
      >
        <div className="w-full max-w-4xl mx-auto flex flex-col justify-between min-h-screen p-4">
          {/* Header */}
          <div className="text-center">
            <Badge
              className="text-2xl px-6 py-3 font-black border-4 border-black mb-6"
              style={{ backgroundColor: "#FDB7EA", color: "#000" }}
            >
              ✨ Battle Complete!
            </Badge>
            <h1 className="text-5xl md:text-7xl font-black text-black mb-4">
              {battleResults.winner_user_id === userId
                ? "🎉 Victory!"
                : "💪 Good Fight!"}
            </h1>
            <p className="text-2xl text-black font-bold mb-8">
              {battleResults.winner_user_id === userId
                ? "You are the champion!"
                : `Winner: ${battleResults.winner_user_id}`}
            </p>

            {/* Battle Summary */}
            <div className="mb-8">
              <div
                className="p-6 rounded-3xl border-4 border-black"
                style={{ backgroundColor: "#FBF3B9" }}
              >
                <h2 className="text-2xl font-black text-black mb-4">
                  Battle Summary
                </h2>
                <p className="text-lg font-bold text-black leading-relaxed">
                  {battleResults.battle_summary}
                </p>
              </div>
            </div>

            {/* Battle Script */}
            {battleResults.battle_script && (
              <div className="mb-8">
                <div
                  className="p-6 rounded-3xl border-4 border-black"
                  style={{ backgroundColor: "#B7B1F2" }}
                >
                  <h2 className="text-2xl font-black text-black mb-4">
                    Battle Story
                  </h2>
                  <div className="text-base font-bold text-black leading-relaxed whitespace-pre-wrap">
                    {battleResults.battle_script}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="text-center space-y-4 pb-12">
            <Button
              onClick={() => (window.location.href = "/")}
              className="w-full md:w-auto text-xl px-8 py-4 rounded-2xl font-black text-black hover:scale-105 transition-all duration-200 border-4 border-black"
              style={{ backgroundColor: "#FDB7EA" }}
            >
              Play Again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
