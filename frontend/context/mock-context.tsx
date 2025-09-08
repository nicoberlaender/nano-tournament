"use client";

import { createContext, useContext, useState } from "react";

interface MockContextType {
  useMock: boolean;
  toggleMock: () => void;
}

const MockContext = createContext<MockContextType | undefined>(undefined);

export function MockProvider({ children }: { children: React.ReactNode }) {
  const [useMock, setUseMock] = useState(false);

  const toggleMock = () => setUseMock((prev) => !prev);

  return (
    <MockContext.Provider value={{ useMock, toggleMock }}>
      {children}
    </MockContext.Provider>
  );
}

export function useMock() {
  const context = useContext(MockContext);
  if (context === undefined) {
    throw new Error("useMock must be used within a MockProvider");
  }
  return context;
}
