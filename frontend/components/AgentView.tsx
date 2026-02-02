'use client'

import { useEffect, useMemo, useRef, useState } from "react";
import AgentCard from "./AgentCard";
import debounce from "lodash/debounce";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { AnimatePresence } from "motion/react";
import { shuffle } from "lodash";
import axios from "axios";

export default function AgentView({ initial }: { initial: Agent[] }) {

    const [agents, setAgents] = useState<Agent[]>(initial);
    const [query, setQuery] = useState<string>("");
    const [skip, setSkip] = useState<number>(0);
    const firstRender = useRef<boolean>(true);

    const getAgents = async (query: string, skip: number) => {
        try {
            const res = await axios.get(`http://localhost:8000/api/agents?query=${encodeURIComponent(query)}&skip=${encodeURIComponent(skip.toString())}`);
            setAgents(res.data);
        }
        catch {

        }
    }

    const debouncedGetAgents = useMemo(
        () => debounce((query: string, skip: number) => getAgents(query ? query.trim() : "", skip), 500),
    []);

    const skipBy = (change: number) => {
        setSkip(v => v + change);
    }

    useEffect(() => {

        if (firstRender.current) {
            firstRender.current = false;
            return;
        }
        debouncedGetAgents(query, skip);
        
        return () => {
            debouncedGetAgents.cancel();
        };

    }, [query, skip, debouncedGetAgents])

    return (
        <>
            <h2 className="text-md sm:text-xl mb-1 text-gray-800 font-semibold">Search</h2>
            <div className='relative mb-4'>
                <input
                    type="text"
                    placeholder="Search..."
                    className={`w-full px-4 py-2.5 rounded-xl border-2 shadow-md border-gray-400/40 focus:border-[#2c81e3] focus:outline-none transition-colors text-gray-800 placeholder:text-gray-400`}
                    onChange={(e) => setQuery(prev => e.target.value.length > 50 ? prev : e.target.value)}
                    maxLength={50}
                />
            </div>
            <div className="grid grid-cols-1 gap-4">
                <AnimatePresence mode="wait">
                    {
                        agents.map((agent, index) => (
                            <AgentCard key={agent.id} agent={agent} index={index} />
                        ))
                    }
                </AnimatePresence>
            </div>
            <div className="w-full mt-5 gap-1 text-gray-400 flex items-center justify-center">
                {
                    (skip !== 0 && query === "") &&
                    <ArrowLeft onClick={() => skipBy(-50)} className="cursor-pointer hover:scale-110 transition-all"/>
                }
                <span>Showing 50 {query == "" ? "per page" : ""}</span>
                {
                    (query === "") &&
                    <ArrowRight onClick={() => skipBy(50)} className="cursor-pointer hover:scale-110 transition-all" />
                }
            </div>
        </>
    );
} 