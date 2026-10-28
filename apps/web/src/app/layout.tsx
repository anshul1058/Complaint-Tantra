import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Complaint-Tantra | AICTE Integrated Complaint Monitoring Dashboard",
  description:
    "AI-powered Integrated Dashboard for Monitoring and Tracking Institution-Related Complaint Cases Across AICTE Bureaus/Cells. Government of India — Ministry of Education.",
  keywords: [
    "AICTE",
    "Complaint Management",
    "Smart India Hackathon",
    "Government of India",
    "Ministry of Education",
  ],
  authors: [{ name: "Team Complaint-Tantra" }],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className="min-h-full flex flex-col bg-[#f8f9fc]">
        {children}
      </body>
    </html>
  );
}
