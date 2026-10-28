import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";

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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400;1,600&family=Playfair+Display:ital,wght@1,500;1,600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col bg-[#F3F7FD] text-slate-900 font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
