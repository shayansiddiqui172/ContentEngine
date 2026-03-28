import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import "./globals.css";
import PinGate from "@/components/PinGate";

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Wealth Capital — Creator Dashboard",
  description: "LinkedIn creator intelligence pipeline",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${dmSans.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col font-sans">
        <PinGate>{children}</PinGate>
      </body>
    </html>
  );
}
