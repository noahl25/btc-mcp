'use client'

import { ArrowRight } from "lucide-react";
import { motion } from "motion/react";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function HeroButton({ className = "" }: { className?: string }) {

    const [hovering, setHovering] = useState<boolean>(false);
    const router = useRouter();

    return (
        <div onClick={() => router.push("/create")} onMouseEnter={() => setHovering(true)} onMouseLeave={() => setHovering(false)} className={`${className} group mx-auto md:mx-0 cursor-pointer pl-3 pr-2 py-2 justify-center items-center w-fit flex gap-2 rounded-full bg-[#2c81e3a8]`}>
            <p className="text-[20px]">Create Your Own</p>
            <div className="size-[30px] overflow-hidden relative group-hover:scale-120 transition-all duration-300 bg-white rounded-full">
                <motion.div 
                    className="absolute left-1/2 -translate-x-[47%] top-1/2 -translate-y-1/2 transform -rotate-45"
                    animate={{
                        x: hovering ? 30 : 0
                    }}
                >
                    <ArrowRight color="black" strokeWidth={1.8} size={21}/>
                </motion.div>
                <motion.div
                    className="absolute left-1/2 -translate-x-[47%] top-1/2 -translate-y-1/2 transform -rotate-45"
                    animate={{
                        x: hovering ? 0 : -30
                    }}
                    initial={{
                        x: -30
                    }}
                >
                    <ArrowRight color="black" strokeWidth={1.8} size={21} />
                </motion.div>
            </div>
        </div>
    );
}   