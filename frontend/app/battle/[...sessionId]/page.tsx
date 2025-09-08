"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Users, Gamepad2, Crown, Sparkles, ImageIcon, Play, Clock } from "lucide-react";

interface Participant {
  id: string;
  name: string;
  joinedAt: Date;
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

  // Mock participants for lobby demo
  useEffect(() => {
    if (gameState === "lobby") {
      const mockParticipants: Participant[] = [
        { id: "1", name: "Alex Chen", joinedAt: new Date(Date.now() - 30000) },
        {
          id: "2",
          name: "Maria Garcia",
          joinedAt: new Date(Date.now() - 25000),
        },
        { id: "3", name: "John Smith", joinedAt: new Date(Date.now() - 20000) },
        { id: "4", name: "Sarah Kim", joinedAt: new Date(Date.now() - 15000) },
      ];

      if (currentPlayer) {
        setParticipants([...mockParticipants, currentPlayer]);
      }
    }
  }, [gameState, currentPlayer]);

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

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));

    const newPlayer: Participant = {
      id: Date.now().toString(),
      name: playerName.trim(),
      joinedAt: new Date(),
    };

    setCurrentPlayer(newPlayer);
    setGameState("lobby");
    setIsJoining(false);
  };

  const handleCreateCharacter = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsCreatingCharacter(true);

    // Simulate API call for character generation
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Mock generated image (in real implementation, this would be from your AI service)
    setGeneratedImage(
      "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 400 400'%3E%3Crect width='400' height='400' fill='%23FBF3B9'/%3E%3Ctext x='200' y='200' text-anchor='middle' dominant-baseline='middle' font-size='20' fill='%23000'%3EGenerated Character%3C/text%3E%3C/svg%3E"
    );
    setIsCreatingCharacter(false);
    setGameState("waiting");
  };

  if (gameState === "join") {
    return (
      <div
        className="min-h-screen flex items-center justify-center p-4"
        style={{ backgroundColor: "#B7B1F2" }}
      >
        <div className="w-full max-w-lg ">
          <Card className="bg-[#FFDCCC] border-none">
            <CardHeader className="text-center p-12">
              <div
                className="w-24 h-24 rounded-3xl flex items-center justify-center mx-auto border-4 border-black"
                style={{ backgroundColor: "#FDB7EA" }}
              >
                <Gamepad2 className="w-12 h-12 text-black" />
              </div>
              <div>
                <CardTitle className="text-5xl text-black mb-4 font-black">
                  Join Battle Arena
                </CardTitle>
                <p className="text-2xl text-black font-bold">
                  Session: {sessionId}
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-12">
              <form onSubmit={handleJoinSession} className="space-y-8">
                <div className="space-y-4">
                  <label className="text-2xl font-bold text-black">
                    Your Battle Name
                  </label>
                  <Input
                    value={playerName}
                    onChange={(e) => setPlayerName(e.target.value)}
                    placeholder="Enter your name"
                    className="text-2xl p-4 border-4 border-black font-bold text-black placeholder:text-gray-600"
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
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (gameState === "lobby") {
    return (
      <div className="min-h-screen p-4" style={{ backgroundColor: "#B7B1F2" }}>
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <Badge
              className="mb-6 text-2xl px-6 py-3 font-black border-4 border-black"
              style={{ backgroundColor: "#FDB7EA", color: "#000" }}
            >
              <Sparkles className="w-6 h-6 mr-2" />
              Battle Lobby
            </Badge>
            <h1 className="text-5xl md:text-7xl font-black text-black mb-4">
              Waiting for Battle to Begin
            </h1>
            <p className="text-3xl text-black font-bold">
              Session: {sessionId}
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <Card
              className="border-4 border-black"
              style={{ backgroundColor: "#FFDCCC" }}
            >
              <CardContent className="flex items-center justify-center p-8">
                <div className="text-center">
                  <Users className="w-12 h-12 text-black mx-auto mb-4" />
                  <div className="text-4xl font-black text-black">
                    {participants.length}
                  </div>
                  <div className="text-xl text-black font-bold">
                    Players Ready
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card
              className="border-4 border-black"
              style={{ backgroundColor: "#FDB7EA" }}
            >
              <CardContent className="flex items-center justify-center p-8">
                <div className="text-center">
                  <Crown className="w-12 h-12 text-black mx-auto mb-4" />
                  <div className="text-4xl font-black text-black">3</div>
                  <div className="text-xl text-black font-bold">Rounds</div>
                </div>
              </CardContent>
            </Card>
            <Card
              className="border-4 border-black"
              style={{ backgroundColor: "#FBF3B9" }}
            >
              <CardContent className="flex items-center justify-center p-8">
                <div className="text-center">
                  <Gamepad2 className="w-12 h-12 text-black mx-auto mb-4" />
                  <div className="text-4xl font-black text-black">AI</div>
                  <div className="text-xl text-black font-bold">
                    Battle Mode
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Participants Grid */}
          <Card
            className="border-4 border-black"
            style={{ backgroundColor: "#FFDCCC" }}
          >
            <CardHeader className="p-8">
              <CardTitle className="text-black flex items-center gap-3 text-3xl font-black">
                <Users className="w-8 h-8" />
                Battle Participants
              </CardTitle>
            </CardHeader>
            <CardContent className="p-8">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {participants.map((participant, index) => (
                  <div
                    key={participant.id}
                    className="flex items-center gap-4 p-6 rounded-2xl border-4 border-black hover:scale-105 transition-all duration-300"
                    style={{ backgroundColor: "#FBF3B9" }}
                  >
                    <Avatar className="w-16 h-16">
                      <AvatarFallback
                        className="text-black font-black text-xl border-2 border-black"
                        style={{ backgroundColor: "#FDB7EA" }}
                      >
                        {participant.name
                          .split(" ")
                          .map((n) => n[0])
                          .join("")
                          .slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-black font-black text-xl">
                          {participant.name}
                        </span>
                        {participant.id === currentPlayer?.id && (
                          <Badge
                            className="text-black font-bold border-2 border-black"
                            style={{ backgroundColor: "#B7B1F2" }}
                          >
                            You
                          </Badge>
                        )}
                        {index === 0 &&
                          participant.id !== currentPlayer?.id && (
                            <Badge
                              className="text-black font-bold border-2 border-black"
                              style={{ backgroundColor: "#FDB7EA" }}
                            >
                              Host
                            </Badge>
                          )}
                      </div>
                      <span className="text-lg text-black font-bold">
                        Joined{" "}
                        {Math.floor(
                          (Date.now() - participant.joinedAt.getTime()) / 1000
                        )}
                        s ago
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Waiting Message with Timer */}
          <div className="text-center mt-12">
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
        className="min-h-screen flex items-center justify-center p-4"
        style={{ backgroundColor: "#B7B1F2" }}
      >
        <div className="w-full max-w-2xl">
          <Card
            className="border-4 border-black shadow-2xl"
            style={{ backgroundColor: "#FFDCCC" }}
          >
            {/* Header */}
            <div className="text-center p-8">
              <Badge
                className="text-xl p-2 font-black border-4 border-black"
                style={{ backgroundColor: "#FDB7EA", color: "#000" }}
              >
                <Sparkles className="w-5 h-5 mr-2" />
                Round 1
              </Badge>
            </div>

            <CardContent className="space-y-8">
              {/* Image Display Area */}
              <div className="w-full aspect-square max-w-md mx-auto">
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
                      <ImageIcon className="w-16 h-16 text-black mx-auto mb-4 opacity-50" />
                      <p className="text-black font-bold text-lg opacity-50">
                        Your character will appear here
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Input and Button Area */}
              <form onSubmit={handleCreateCharacter} className="space-y-6">
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
                <Button
                  onClick={() =>
                    handleCreateCharacter(new Event("submit") as any)
                  }
                  className="w-full text-xl py-4 rounded-2xl font-black text-black hover:scale-105 transition-all duration-200 border-4 border-black"
                  style={{ backgroundColor: "#B7B1F2" }}
                >
                  Regenerate Character
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (gameState === "waiting") {
    return (
      <div
        className="min-h-screen flex items-center justify-center p-4"
        style={{ backgroundColor: "#B7B1F2" }}
      >
        <div className="w-full max-w-2xl">
          <Card
            className="border-4 border-black shadow-2xl"
            style={{ backgroundColor: "#FFDCCC" }}
          >
            {/* Header */}
            <div className="text-center p-8">
              <Badge
                className="text-xl p-2 font-black border-4 border-black mb-6"
                style={{ backgroundColor: "#FDB7EA", color: "#000" }}
              >
                <Sparkles className="w-5 h-5 mr-2" />
                Round 1
              </Badge>
              <h1 className="text-4xl md:text-5xl font-black text-black mb-4">
                Character Ready!
              </h1>
              <p className="text-xl text-black font-bold">
                Waiting for all players to finish...
              </p>
            </div>

            <CardContent className="p-8 space-y-8">
              {/* Display the generated character */}
              <div className="w-full aspect-square max-w-md mx-auto">
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

              {/* Waiting timer */}
              <div className="text-center">
                <div
                  className="inline-flex items-center gap-4 px-8 py-4 rounded-2xl border-4 border-black"
                  style={{ backgroundColor: "#B7B1F2" }}
                >
                  <Clock className="w-6 h-6 text-black" />
                  <span className="text-black font-black text-xl">
                    Battle starting in {waitingTimer} seconds...
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (gameState === "battle") {
    return (
      <>
        <style jsx>{`
          @keyframes slide {
            0% { transform: translateX(0); }
            100% { transform: translateX(40px); }
          }
        `}</style>
        <div
          className="min-h-screen"
          style={{ backgroundColor: "#B7B1F2" }}
        >
        {/* Battle Header - Player vs Player */}
        <div className="w-full p-6 border-b-4 border-black" style={{ backgroundColor: "#FFDCCC" }}>
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            {/* Player 1 */}
            <div className="flex items-center gap-4">
              <Avatar className="w-16 h-16">
                <AvatarFallback
                  className="text-black font-black text-xl border-4 border-black"
                  style={{ backgroundColor: "#FDB7EA" }}
                >
                  {currentPlayer?.name.split(" ").map(n => n[0]).join("").slice(0, 2)}
                </AvatarFallback>
              </Avatar>
              <div>
                <div className="text-2xl font-black text-black">{currentPlayer?.name}</div>
                <div className="text-lg font-bold text-black opacity-75">You</div>
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
                <div className="text-2xl font-black text-black">Alex Chen</div>
                <div className="text-lg font-bold text-black opacity-75">Opponent</div>
              </div>
              <Avatar className="w-16 h-16">
                <AvatarFallback
                  className="text-black font-black text-xl border-4 border-black"
                  style={{ backgroundColor: "#B7B1F2" }}
                >
                  AC
                </AvatarFallback>
              </Avatar>
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
                  background: "linear-gradient(45deg, #FDB7EA 25%, #FBF3B9 25%, #FBF3B9 50%, #FDB7EA 50%, #FDB7EA 75%, #FBF3B9 75%)",
                  backgroundSize: "40px 40px",
                  animation: "slide 2s linear infinite"
                }}
              />
              
              {/* Play indicator */}
              <div className="text-center z-10">
                <div 
                  className="w-24 h-24 rounded-full flex items-center justify-center mb-4 mx-auto border-4 border-white"
                  style={{ backgroundColor: "#FDB7EA" }}
                >
                  <Play className="w-12 h-12 text-black ml-1" />
                </div>
                <p className="text-white font-black text-2xl">Battle in Progress</p>
                <p className="text-white font-bold text-lg opacity-75">Epic showdown between characters!</p>
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
              <Sparkles className="w-5 h-5 mr-2" />
              Round 1 of 3
            </Badge>
          </div>
        </div>
      </div>
      </>
    );
  }

  return null;
}
