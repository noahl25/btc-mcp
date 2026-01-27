'use client'

import { useEffect, useRef, useState } from "react";
import { motion } from 'framer-motion'
import Image from "next/image";
import { useRouter } from "next/navigation";

type CursorState = {
    width: number,
    opacity: number,
    left: number,
    scale: number
}

const CursorBackground = ({ state }: { state: CursorState }) => (
    <motion.div animate={state} className='absolute -z-5 rounded-[10px] bg-white/20 top-[3px] bottom-[3px]' />
)

const NavbarElement = ({ name, setCursorState, onClick }: { name: string, setCursorState: (_: CursorState) => void, onClick: () => void}) => {

    const ref = useRef<HTMLDivElement | null>(null);
    const [initialWidth, setInitialWidth] = useState<number>(0);

    useEffect(() => {
        setInitialWidth(ref.current?.getBoundingClientRect().width ?? 0);
    }, [])

    return (
        <motion.div
            className='w-fit px-2.25 h-full'
            ref={ref}
            onMouseEnter={() => {
                setCursorState({
                    width: initialWidth,
                    opacity: 1,
                    left: ref.current?.offsetLeft ?? 0,
                    scale: 1
                });
            }}
            onClick={onClick}
            whileTap={{
                scale: 0.85,
            }}
        >
            <p className='text-sm z-10 md:text-lg font-semibold text-white cursor-pointer tracking-wide'>
                {name}
            </p>
        </motion.div>
    );
}

export default function Navbar() {

    const [cursorState, setCursorState] = useState<CursorState>({
        width: 0,
        left: 0,
        opacity: 0,
        scale: 1
    });

    const router = useRouter();

    return (
        <div onMouseLeave={() => { setCursorState({ ...cursorState, opacity: 0 }) }} className="absolute z-50 flex overflow-hidden left-1/2 -translate-x-1/2 top-[35px] bg-white/20 border-white/20 border-1 border-2 rounded-[12px]">
           <div className="w-[50px] border-r-2 border-white/20 bg-no-repeat bg-center bg-contain relative ml-1" style={{
                backgroundImage: `url("/assets/images/icon-dark.png")`,
           }}>
           </div>
           <div className="py-[5px] px-[3px] flex">
                <NavbarElement setCursorState={setCursorState} onClick={() => router.push("/")} name="Home" />
                <NavbarElement setCursorState={setCursorState} onClick={() => router.push("/explore")} name="Explore" />
                <NavbarElement setCursorState={setCursorState} onClick={() => router.push("/create")} name="Create" />
                <CursorBackground state={cursorState} />
            </div>
        </div>
    );
}