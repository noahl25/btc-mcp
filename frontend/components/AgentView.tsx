'use client'

import { useEffect, useMemo, useRef, useState } from "react";
import AgentCard from "./AgentCard";
import debounce from "lodash/debounce";
import { ALargeSmall, ArrowLeft, ArrowRight, Pin, Trophy } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { shuffle } from "lodash";
import axios from "axios";

export default function AgentView({ initial }: { initial: Agent[] }) {

    const [agents, setAgents] = useState<Agent[]>(initial);
    const [query, setQuery] = useState<string>("");
    const [skip, setSkip] = useState<number>(0);
    const [resultKey, setResultKey] = useState<number>(0);
    const [exactSearch, setExactSearch] = useState<boolean>(false);
    const [mostStaked, setMostStaked] = useState<boolean>(false);
    const firstRender = useRef<boolean>(true);

    const getAgents = async (query: string, skip: number, exact_search: boolean, most_staked: boolean) => {
        try {
            const res = await axios.get(`http://localhost:8000/api/agents?query=${encodeURIComponent(query)}&skip=${encodeURIComponent(skip.toString())}&exact_search=${encodeURIComponent(exact_search)}&sort_by=${encodeURIComponent(most_staked ? "staked" : "date")}`);
            setAgents(res.data);
            setResultKey(prev => prev + 1);
        }
        catch {

        }
    }

    const debouncedGetAgents = useMemo(
        () => debounce((query: string, skip: number, exact_search: boolean, most_staked: boolean) => getAgents(query ? query.trim() : "", skip, exact_search, most_staked), 500),
    []);

    const skipBy = (change: number) => {
        setSkip(v => v + change);
    }

    useEffect(() => {

        if (firstRender.current) {
            firstRender.current = false;
            return;
        }
        debouncedGetAgents(query, skip, exactSearch, mostStaked);
        
        return () => {
            debouncedGetAgents.cancel();
        };

    }, [query, skip, debouncedGetAgents, exactSearch, mostStaked])

    return (
        <>
            <h2 className="text-md sm:text-xl mb-1 text-gray-800 font-semibold">Search</h2>
            <div className='relative mb-4 transition-colors rounded-xl border-2 shadow-md border-gray-400/40'>
                <input
                    type="text"
                    placeholder="Search..."
                    className={`w-full px-4 py-2.5 text-gray-800 focus:outline-none placeholder:text-gray-400`}
                    onChange={(e) => setQuery(prev => e.target.value.length > 50 ? prev : e.target.value)}
                    maxLength={50}
                />
                <div className="absolute top-1/2 -translate-y-1/2 right-2 flex items-center justify-center gap-2">
                    <div title="Exact search" onClick={() => setExactSearch(v => !v)} className={`transition-colors ${!exactSearch ? "bg-gray-200 text-gray-400" : "bg-[#2c81e3]/20 text-[#2c81e3]"} py-1 px-2 cursor-pointer rounded-xl grid place-items-center`}>
                        <ALargeSmall/>
                    </div>
                    <div title="Sort by most staked" onClick={() => setMostStaked(v => !v)} className={`transition-colors ${!mostStaked ? "bg-gray-200 text-gray-400" : "bg-[#2c81e3]/20 text-[#2c81e3]"} py-1 px-2 cursor-pointer rounded-xl grid place-items-center`}>
                        <Trophy />
                    </div>
                </div>
            </div>
            <div>
                <AnimatePresence mode="wait">
                    <div key={resultKey} className="grid grid-cols-1 gap-4">
                        {
                            agents.map((agent, index) => (
                                <AgentCard key={agent.id} agent={agent} index={index} />
                            ))
                        }
                    </div>
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