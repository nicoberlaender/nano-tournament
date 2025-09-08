"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Users, Gamepad2, Crown, Sparkles } from "lucide-react";

interface Participant {
  id: string;
  name: string;
  joinedAt: Date;
}

type GameState = "join" | "lobby" | "battle" | "results";

export default function BattleSession() {
  const params = useParams();
  const sessionId = Array.isArray(params.sessionId) ? params.sessionId[0] : params.sessionId;
  
  const [gameState, setGameState] = useState<GameState>("join");
  const [playerName, setPlayerName] = useState("");
  const [currentPlayer, setCurrentPlayer] = useState<Participant | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [isJoining, setIsJoining] = useState(false);

  // Mock participants for lobby demo
  useEffect(() => {
    if (gameState === "lobby") {
      const mockParticipants: Participant[] = [
        { id: "1", name: "Alex Chen", joinedAt: new Date(Date.now() - 30000) },
        { id: "2", name: "Maria Garcia", joinedAt: new Date(Date.now() - 25000) },
        { id: "3", name: "John Smith", joinedAt: new Date(Date.now() - 20000) },
        { id: "4", name: "Sarah Kim", joinedAt: new Date(Date.now() - 15000) },
      ];
      
      if (currentPlayer) {
        setParticipants([...mockParticipants, currentPlayer]);
      }
    }
  }, [gameState, currentPlayer]);

  const handleJoinSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!playerName.trim()) return;

    setIsJoining(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const newPlayer: Participant = {
      id: Date.now().toString(),
      name: playerName.trim(),
      joinedAt: new Date()
    };
    
    setCurrentPlayer(newPlayer);
    setGameState("lobby");
    setIsJoining(false);
  };

  if (gameState === "join") {
    return (
      <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: '#B7B1F2' }}>
        <div className="w-full max-w-lg">
          <Card className="border-4 border-black shadow-2xl" style={{ backgroundColor: '#FFDCCC' }}>
            <CardHeader className="text-center space-y-8 p-12">
              <div className="w-24 h-24 rounded-3xl flex items-center justify-center mx-auto border-4 border-black" style={{ backgroundColor: '#FDB7EA' }}>
                <Gamepad2 className="w-12 h-12 text-black" />
              </div>
              <div>
                <CardTitle className="text-5xl text-black mb-4 font-black">Join Battle Arena</CardTitle>
                <p className="text-2xl text-black font-bold">Session: {sessionId}</p>
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
                    style={{ backgroundColor: '#FBF3B9' }}
                    maxLength={20}
                    required
                  />
                </div>
                <Button 
                  type="submit" 
                  disabled={!playerName.trim() || isJoining}
                  className="w-full text-2xl py-6 rounded-2xl font-black text-black hover:scale-105 transition-all duration-200 border-4 border-black"
                  style={{ backgroundColor: '#FDB7EA' }}
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
      <div className="min-h-screen p-4" style={{ backgroundColor: '#B7B1F2' }}>
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <Badge className="mb-6 text-2xl px-6 py-3 font-black border-4 border-black" style={{ backgroundColor: '#FDB7EA', color: '#000' }}>
              <Sparkles className="w-6 h-6 mr-2" />
              Battle Lobby
            </Badge>
            <h1 className="text-5xl md:text-7xl font-black text-black mb-4">
              Waiting for Battle to Begin
            </h1>
            <p className="text-3xl text-black font-bold">Session: {sessionId}</p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <Card className="border-4 border-black" style={{ backgroundColor: '#FFDCCC' }}>
              <CardContent className="flex items-center justify-center p-8">
                <div className="text-center">
                  <Users className="w-12 h-12 text-black mx-auto mb-4" />
                  <div className="text-4xl font-black text-black">{participants.length}</div>
                  <div className="text-xl text-black font-bold">Players Ready</div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-4 border-black" style={{ backgroundColor: '#FDB7EA' }}>
              <CardContent className="flex items-center justify-center p-8">
                <div className="text-center">
                  <Crown className="w-12 h-12 text-black mx-auto mb-4" />
                  <div className="text-4xl font-black text-black">3</div>
                  <div className="text-xl text-black font-bold">Rounds</div>
                </div>
              </CardContent>
            </Card>
            <Card className="border-4 border-black" style={{ backgroundColor: '#FBF3B9' }}>
              <CardContent className="flex items-center justify-center p-8">
                <div className="text-center">
                  <Gamepad2 className="w-12 h-12 text-black mx-auto mb-4" />
                  <div className="text-4xl font-black text-black">AI</div>
                  <div className="text-xl text-black font-bold">Battle Mode</div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Participants Grid */}
          <Card className="border-4 border-black" style={{ backgroundColor: '#FFDCCC' }}>
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
                    style={{ backgroundColor: '#FBF3B9' }}
                  >
                    <Avatar className="w-16 h-16">
                      <AvatarFallback className="text-black font-black text-xl border-2 border-black" style={{ backgroundColor: '#FDB7EA' }}>
                        {participant.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-black font-black text-xl">{participant.name}</span>
                        {participant.id === currentPlayer?.id && (
                          <Badge className="text-black font-bold border-2 border-black" style={{ backgroundColor: '#B7B1F2' }}>
                            You
                          </Badge>
                        )}
                        {index === 0 && participant.id !== currentPlayer?.id && (
                          <Badge className="text-black font-bold border-2 border-black" style={{ backgroundColor: '#FDB7EA' }}>
                            Host
                          </Badge>
                        )}
                      </div>
                      <span className="text-lg text-black font-bold">
                        Joined {Math.floor((Date.now() - participant.joinedAt.getTime()) / 1000)}s ago
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Waiting Message */}
          <div className="text-center mt-12">
            <div className="inline-flex items-center gap-4 px-8 py-4 rounded-2xl border-4 border-black" style={{ backgroundColor: '#FDB7EA' }}>
              <div className="w-4 h-4 rounded-full animate-pulse" style={{ backgroundColor: '#B7B1F2' }}></div>
              <span className="text-black font-black text-2xl">Waiting for host to start the battle...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}