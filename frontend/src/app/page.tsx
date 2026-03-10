"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Gamepad2, Video, Sparkles, Upload, Zap, TrendingUp, Clock } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Navbar */}
      <nav className="navbar-glass sticky top-0 z-50 flex justify-between items-center px-6 sm:px-12 md:px-20 py-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center shadow-lg shadow-purple-500/30">
            <Sparkles className="text-white w-4 h-4" />
          </div>
          <span className="text-base font-bold tracking-tight text-white">AI Shorts</span>
        </div>
        <nav className="hidden sm:flex items-center gap-1 text-sm font-medium">
          <Link href="/" className="px-4 py-2 rounded-lg text-white bg-white/5 transition-colors">Dashboard</Link>
          <a href="#games" className="px-4 py-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5 transition-colors">Games</a>
          <a href="#" className="px-4 py-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5 transition-colors">Settings</a>
        </nav>
        <Link
          href="/upload"
          className="btn-premium flex items-center gap-2 text-sm px-5 py-2.5 rounded-xl"
        >
          <Upload className="w-4 h-4" />
          New Project
        </Link>
      </nav>

      <main className="flex-1 px-6 sm:px-12 md:px-20 pb-20">
        {/* Hero */}
        <section className="pt-20 pb-16 text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 glow-badge px-4 py-1.5 rounded-full text-sm font-medium mb-8"
          >
            <Zap className="w-3.5 h-3.5" />
            Powered by Generative AI
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.6 }}
            className="text-5xl sm:text-7xl font-extrabold tracking-tight mb-6 leading-[1.08]"
          >
            <span className="gradient-text">Turn Gameplay</span>
            <br />
            <span className="gradient-text-primary">into Viral Shorts</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="text-lg text-zinc-400 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Upload long gaming sessions. Our AI finds the best moments, generates
            influencer-style reactions, and creates ready-to-publish vertical videos — in minutes.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link
              href="/upload"
              className="btn-premium h-13 px-8 py-3.5 rounded-2xl text-base flex items-center gap-2.5"
            >
              <Upload className="w-5 h-5" />
              Start Creating
            </Link>
            <button className="btn-secondary h-13 px-8 py-3.5 rounded-2xl text-base flex items-center gap-2.5 font-medium">
              <Video className="w-5 h-5" />
              View Renders
            </button>
          </motion.div>
        </section>

        {/* Stats */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="max-w-3xl mx-auto grid grid-cols-3 gap-4 mb-20"
        >
          {[
            { label: "Avg. Time Saved", value: "4h+", icon: <Clock className="w-4 h-4 text-purple-400" /> },
            { label: "Clips Generated", value: "10K+", icon: <Video className="w-4 h-4 text-pink-400" /> },
            { label: "Viral Rate", value: "68%", icon: <TrendingUp className="w-4 h-4 text-green-400" /> },
          ].map((stat) => (
            <div key={stat.label} className="glass rounded-2xl p-5 text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                {stat.icon}
                <span className="text-2xl font-bold text-white">{stat.value}</span>
              </div>
              <p className="text-xs text-zinc-500 font-medium uppercase tracking-wide">{stat.label}</p>
            </div>
          ))}
        </motion.section>

        {/* Games */}
        <section id="games" className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-white">Supported Games</h2>
              <p className="text-zinc-500 text-sm mt-1">Pick a game to get started</p>
            </div>
            <span className="text-xs text-zinc-600 font-medium">More coming soon</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <GameCard
              title="Valorant"
              desc="Process competitive matches and extract clutch rounds, aces, and highlight plays."
              accentColor="text-red-400"
              gradientFrom="from-red-500/10"
              gradientTo="to-orange-500/5"
              borderHover="hover:border-red-500/30"
              delay={0.45}
            />
            <GameCard
              title="Fortnite"
              desc="Extract Victory Royales, epic builds, and highlight eliminations automatically."
              accentColor="text-blue-400"
              gradientFrom="from-blue-500/10"
              gradientTo="to-cyan-500/5"
              borderHover="hover:border-blue-500/30"
              delay={0.5}
            />
            <GameCard
              title="Apex Legends"
              desc="Find the perfect clutches, triple kills, and champion moments in your footage."
              accentColor="text-orange-400"
              gradientFrom="from-orange-500/10"
              gradientTo="to-red-500/5"
              borderHover="hover:border-orange-500/30"
              delay={0.55}
            />
          </div>
        </section>
      </main>
    </div>
  );
}

interface GameCardProps {
  title: string;
  desc: string;
  accentColor: string;
  gradientFrom: string;
  gradientTo: string;
  borderHover: string;
  delay: number;
}

function GameCard({ title, desc, accentColor, gradientFrom, gradientTo, borderHover, delay }: GameCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
    >
      <Link href="/upload">
        <div className={`glass rounded-2xl p-6 flex flex-col gap-5 cursor-pointer ${borderHover} transition-all group h-full`}>
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${gradientFrom} ${gradientTo} border border-white/5 flex items-center justify-center group-hover:scale-105 transition-transform`}>
            <Gamepad2 className={`w-6 h-6 ${accentColor}`} />
          </div>
          <div className="flex-1">
            <h3 className="text-base font-semibold text-white mb-1.5">{title}</h3>
            <p className="text-sm text-zinc-500 leading-relaxed">{desc}</p>
          </div>
          <div className={`flex items-center gap-1.5 text-xs font-medium ${accentColor} opacity-70 group-hover:opacity-100 transition-opacity`}>
            <Upload className="w-3 h-3" />
            Upload footage
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
