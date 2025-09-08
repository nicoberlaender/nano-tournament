import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { MockProvider } from "@/context/mock-context";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Documentation Journey",
  description: "Interactive AI-powered documentation explorer",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <MockProvider>{children}</MockProvider>
      </body>
    </html>
  );
}
