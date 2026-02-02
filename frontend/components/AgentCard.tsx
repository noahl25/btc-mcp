'use client'

import { motion } from "motion/react";
import { useRouter } from "next/navigation";

export default function AgentCard({ agent, index }: { agent: Agent, index: number }) {

    const truncatedDescription = agent.description.length > 500 ? agent.description.slice(0, 500) + "..." : agent.description;
    const router = useRouter();

    return (
        <motion.div onClick={() => router.push(`/explore/${agent.id}`)} exit={{ opacity: 0, x: 10 }} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} whileHover={{ y: -3, transition: { delay: 0, ease: "easeInOut", duration: 0.5 } }} transition={{ delay: index * 0.05, duration: 0.5, ease: "easeInOut" }} className="border relative border-gray-200 rounded-xl shadow-md hover:shadow-xl border-2 border-gray-400/40 transition-shadow duration-500 ease-in-out cursor-pointer">
            <div className="px-6 py-5">
                <h3 className="text-xl font-semibold text-gray-800">{agent.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{truncatedDescription}</p>
                <div className="flex flex-wrap gap-1.5 mt-3">
                    {
                        Object.keys(agent.tools).map((toolName) => (
                            <span 
                                key={toolName} 
                                className="px-2 py-1 text-xs font-medium bg-gray-400/20 text-gray-600 rounded-full"
                            >
                                {toolName}
                            </span>
                        ))
                    }
                </div>
            </div>
            <div className="flex items-center justify-between mt-4 pt-3 px-6 pt-5 pb-5 border-t-2 border-gray-400/40">
                <span className="text-sm text-gray-500">
                    by <span className="font-medium text-gray-700">{agent.creator}</span>
                </span>
                <span className="text-sm font-medium text-[#2c81e3]">
                    {agent.cost_per_token} credits/token
                </span>
            </div>
            <div className="absolute top-2 right-3 text-gray-600 text-sm">
                {new Date(agent.date).toLocaleDateString()}
            </div>
        </motion.div>
    );
}