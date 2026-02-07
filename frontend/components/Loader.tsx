import { useAnimationControls, motion } from "motion/react";
import { useState, useEffect } from "react";

export default function Loader({ state }: { state: "loading" | "complete" | "failed" }) {

    const checkAnimationControls = useAnimationControls();
    const xAnimationControls = useAnimationControls();
    const [showIcon, setShowIcon] = useState(false);

    const dotVariants = {
        loading: (i: number) => ({
            y: [0, -12, 0],
            backgroundColor: "#2c81e3",
            transition: {
                y: {
                    repeat: Infinity,
                    duration: 1,
                    ease: "easeInOut" as const,
                    delay: i * 0.15,
                },
            },
        }),
        complete: {
            y: 0,
            scale: [1, 1.3, 0],
            backgroundColor: "#2c81e3",
            transition: {
                duration: 0.4,
                ease: "easeOut" as const,
            },
        },
        failed: {
            y: 0,
            scale: [1, 1.3, 0],
            backgroundColor: "#ef4444",
            transition: {
                duration: 0.4,
                ease: "easeOut" as const,
            },
        },
    };

    useEffect(() => {
        if (state === "complete") {
            setTimeout(() => {
                setShowIcon(true);
                checkAnimationControls.start({
                    pathLength: 1,
                    opacity: 1,
                    transition: {
                        pathLength: { type: "spring", duration: 0.8, bounce: 0 },
                        opacity: { duration: 0.01 },
                    },
                });
            }, 400);
        }
        else if (state === "failed") {
            setTimeout(() => {
                setShowIcon(true);
                xAnimationControls.start({
                    pathLength: 1,
                    opacity: 1,
                    transition: {
                        pathLength: { type: "spring", duration: 0.8, bounce: 0 },
                        opacity: { duration: 0.01 },
                    },
                });
            }, 400);
        }
        else {
            setShowIcon(false);
        }
    }, [state]);

    return (
        <div className="relative size-16 flex items-center justify-center">
            <div className={`flex gap-2 items-center justify-center ${showIcon ? 'hidden' : ''}`}>
                {[0, 1, 2].map((i) => (
                    <motion.div
                        key={i}
                        custom={i}
                        variants={dotVariants}
                        animate={state}
                        className="size-3 rounded-full bg-[#2c81e3]"
                    />
                ))}
            </div>
            <motion.div
                initial={{ scale: 0, opacity: 0 }}
                animate={state === "complete" && showIcon ? { scale: 1, opacity: 1 } : {}}
                transition={{ type: "spring", duration: 0.5, bounce: 0.4 }}
                className="absolute inset-0 flex items-center justify-center"
            >
                <div className="size-14 rounded-full bg-[#2c81e3]/10 flex items-center justify-center">
                    <motion.svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="32"
                        height="32"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#2c81e3"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <motion.path
                            animate={checkAnimationControls}
                            d="M4 12 9 17 20 6"
                            initial={{ pathLength: 0, opacity: 0 }}
                        />
                    </motion.svg>
                </div>
            </motion.div>
            <motion.div
                initial={{ scale: 0, opacity: 0 }}
                animate={state === "failed" && showIcon ? { scale: 1, opacity: 1 } : {}}
                transition={{ type: "spring", duration: 0.5, bounce: 0.4 }}
                className="absolute inset-0 flex items-center justify-center"
            >
                <div className="size-14 rounded-full bg-red-500/10 flex items-center justify-center">
                    <motion.svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="32"
                        height="32"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#ef4444"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <motion.path
                            animate={xAnimationControls}
                            initial={{ pathLength: 0, opacity: 0 }}
                            d="M18 6 6 18"
                        />
                        <motion.path
                            animate={xAnimationControls}
                            initial={{ pathLength: 0, opacity: 0 }}
                            d="m6 6 12 12"
                        />
                    </motion.svg>
                </div>
            </motion.div>
        </div>
    );
}