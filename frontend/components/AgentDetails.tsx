"use client";

import { Bitcoin, Check, Coins, Copy, TrendingUp, Trophy, X, Zap } from "lucide-react";
import { AnimatePresence, motion, useAnimationControls } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useAuth } from "./AuthContext";
import QRCode from "qrcode";
import axios from "axios";
import bolt11 from "bolt11";
import { useRouter } from "next/navigation";

function CopyableField({ label, value }: { label: string; value: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        await navigator.clipboard.writeText(value);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="flex items-center justify-between py-3 border-b border-gray-200 last:border-b-0">
            <span className="text-gray-500 text-sm shrink-0">{label}</span>
            <div className="flex items-center gap-2 min-w-0">
                <code className="text-gray-800 text-sm bg-gray-100 px-2 py-1 rounded truncate">
                    {value}
                </code>
                <button
                    onClick={handleCopy}
                    className="text-[#2c81e3] hover:text-[#1a5fb4] text-sm font-medium transition-colors cursor-pointer"
                >
                    {
                        copied ?
                        <div className="grid place-items-center bg-gray-100 p-2 rounded-md">
                            <Check size={15}/>
                        </div>
                        :
                        <div className="grid place-items-center bg-gray-100 p-2 rounded-md">
                            <Copy size={15} />
                        </div>
                    }
                </button>
            </div>
        </div>
    );
}

function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div className="flex items-center justify-between py-3 border-b border-gray-200 last:border-b-0">
            <span className="text-gray-500 text-sm">{label}</span>
            <div className="text-gray-800 text-sm">{children}</div>
        </div>
    );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
    return (
        <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            {children}
        </h2>
    );
}

function ToolDocstring({ name, docstring }: { name: string; docstring: string }) {

    const formattedDocstring = docstring.replace(/\\n/g, '\n').replace(/\\t/g, '    ');

    return (
        <div className="border-2 border-gray-400/40 rounded-xl overflow-hidden">
            <div className="bg-gray-100 px-4 py-2.5 border-b-2 border-gray-400/40">
                <span className="font-mono text-sm font-medium text-gray-800">{name}</span>
            </div>
            <pre className="p-4 text-gray-700 text-sm font-mono whitespace-pre-wrap bg-white overflow-x-auto">
                {formattedDocstring}
            </pre>
        </div>
    );
}

const SubmissionScreen = ({ offer, close, id }: { offer: string, close: () => void, id: string }) => {
    const [loadingState, setLoadingState] = useState<"loading" | "complete" | "failed">("loading");
    const [state, setState] = useState<"paying" | "processing">("paying");
    const [showQRCode, setShowQRCode] = useState<boolean>(false);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const [invoiceID, setInvoiceID] = useState<string | null>(null);
    const [sats, setSats] = useState<string>("Unknown");

    const router = useRouter();

    useEffect(() => {
        let pollInterval: any = null;
        const func = async () => {
            if (state == "paying") {
                const res = await axios.post("http://localhost:8000/api/payments/stake",
                    { offer_id: offer, agent_id: id },
                    { withCredentials: true }
                );
                setInvoiceID(res.data);
                if (canvasRef.current) {
                    QRCode.toCanvas(canvasRef.current, res.data);
                    setShowQRCode(true);
                }
                setSats(String(bolt11.decode(res.data).satoshis as number));
                pollInterval = setInterval(async () => {
                    const pollRes = await axios.get(`http://localhost:8000/api/payments/payment-complete/${encodeURIComponent(res.data)}`);
                    if (pollRes.data.status === true) {
                        clearInterval(pollInterval!);
                        setLoadingState("complete");
                        setState("processing");
                        setTimeout(() => { router.refresh(); close(); }, 2000);
                    }
                }, 3000);
            }
        }
        func();
        return () => clearInterval(pollInterval);
    }, [])

    return (
        <AnimatePresence mode="wait">
            {
                state == "paying" ?
                <motion.div exit={{ opacity: 0 }} initial={{ opacity: 1 }} key="initial">
                    <div onClick={close} className='absolute p-1 cursor-pointer group hover:bg-red-500/20 text-gray-400 hover:text-red-500 transition-all top-2 right-2 size-6 rounded-full bg-gray-400/10 flex items-center justify-center z-10'>
                        <X />
                    </div>
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: showQRCode ? 1 : 0 }} className='w-full pt-5 h-[350px] flex items-center justify-center'>
                        <canvas ref={canvasRef} className='w-fit h-fit' />
                    </motion.div>
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: showQRCode ? 1 : 0 }} className='text-center text-gray-800 pb-5'>
                        <div>
                            Pay using your Lightning wallet.
                        </div>
                        <div className='text-xs text-gray-400'>
                            Amount due: {sats} SATS.
                        </div>
                    </motion.div>
                </motion.div>
                    :
                <motion.div className='my-7 h-[350px]' key="check">
                    <div className='flex h-full w-full items-center justify-center'>
                        <motion.div
                            initial={{ scale: 0, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ type: "spring", duration: 0.5, bounce: 0.4 }}
                            className="flex items-center justify-center"
                            key="check"
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
                                        animate={{
                                            pathLength: 1,
                                            opacity: 1
                                        }}
                                        transition={{
                                            pathLength: {type: "spring", duration: 0.8, bounce: 0 },
                                            opacity: {duration: 0.01 },
                                        }}
                                        d="M4 12 9 17 20 6"
                                        initial={{ pathLength: 0, opacity: 0 }}
                                    />
                                </motion.svg>
                            </div>
                        </motion.div>
                    </div>
                </motion.div>   
            }
        </AnimatePresence>
    );
}

const AuthenticationScreen = ({ close }: { close: () => void }) => {

    const [showQRCode, setShowQRCode] = useState<boolean>(false);
    const [complete, setComplete] = useState<boolean>(false);
    const [k1, setK1] = useState<string | null>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);

    const { setAuthenticated } = useAuth();

    useEffect(() => {
        async function fetchLNURL() {
            const res = await axios.get("http://localhost:8000/creator/creator-signin", {
                withCredentials: true
            });
            setK1(res.data.k1);
            if (canvasRef.current) {
                QRCode.toCanvas(canvasRef.current, res.data.lnurl);
                setShowQRCode(true);
            }
        }
        fetchLNURL();
    }, []);

    useEffect(() => {

        if (!k1) return;

        const id = setInterval(async () => {
            const res = await axios.post("http://localhost:8000/creator/creator-poll", 
                { k1 },
                { withCredentials: true }
            );
            if (res.data.status === "success") {
                setComplete(true);
                setAuthenticated(true);
                clearInterval(id);
            }
        }, 3000);

        return () => clearInterval(id);

    }, [k1]);

    const checkAnimationControls = useAnimationControls();
    useEffect(() => {

        if (complete) {
            const timeout = setTimeout(() => {
                checkAnimationControls.start({
                    pathLength: 1,
                    opacity: 1,
                    transition: {
                        pathLength: { type: "spring", duration: 0.8, bounce: 0 },
                        opacity: { duration: 0.01 },
                    },
                }).then(() => {
                    setTimeout(close, 1500);
                });
            }, 500);
            return () => clearTimeout(timeout);
        }

    }, [complete]);
    
    return (
        <>
            <div onClick={close} className='absolute p-1 cursor-pointer group hover:bg-red-500/20 text-gray-400 hover:text-red-500 transition-all top-2 right-2 size-6 rounded-full bg-gray-400/10 flex items-center justify-center z-10'>
                <X/>
            </div>
            <AnimatePresence mode='popLayout'>
            {
                !complete ?
                <motion.div 
                    key="initial"
                    initial={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col items-center justify-center"
                >
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: showQRCode ? 1 : 0 }} className='w-full flex items-center justify-center'>
                        <canvas ref={canvasRef} className='w-full h-full'/>
                    </motion.div>
                    <div className='text-center text-gray-800 pb-3'>
                        <div>
                            Authenticate using your Lightning wallet.
                        </div>
                        <div className='text-xs text-gray-400'>
                            This will be used to return your stake to you.
                        </div>
                    </div>
                </motion.div>
                :
                <motion.div
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: "spring", duration: 0.5, bounce: 0.4 }}
                    className="flex items-center justify-center"
                    key="check"
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
            }
            </AnimatePresence>
        </>
    );
}

const StakingScreen = ({ setOffer, close }: { setOffer: (v: string) => void, close: () => void }) => {

    const STAKE_OPTIONS = [
        { amount: 100, label: "Starter", sub: "Like it", icon: <TrendingUp className="size-5" />, color: "bg-blue-500", id: "b5bc8ce8-a93e-4ef2-991a-d7c0700af962" },
        { amount: 1000, label: "Pro", sub: "Love it", icon: <Zap className="size-5" />, color: "bg-indigo-600", featured: false, id: "b5bc82e8-a93e-4ef2-9914-d7c3750af962" },
        { amount: 10000, label: "Whale", sub: "Gotta have it", icon: <Bitcoin className="size-5" />, color: "bg-purple-600", id: "8fd9b383-0325-4461-bf35-45a278bbc025" },
    ];

    return (
        <>
            <button
                onClick={close}
                className="absolute cursor-pointer top-4 right-4 p-2 rounded-full bg-gray-100 text-gray-500 hover:bg-red-50 hover:text-red-500 transition-colors z-20"
            >
                <X size={18} />
            </button>
            <div className="pt-10 px-8 text-center bg-gradient-to-b from-indigo-50/50 to-white">
                <div className="inline-flex items-center justify-center p-3 rounded-2xl bg-[#2c81e3a8] text-white mb-4 shadow-lg shadow-indigo-200">
                    <Coins size={28} />
                </div>
                <h2 className="text-2xl font-bold text-gray-900">Stake Credits</h2>
                <p className="text-gray-500 mt-1 text-sm">Lock your credits to show support and help others find this server!</p>
            </div>
            <div className="p-6 flex flex-col gap-4">
                {STAKE_OPTIONS.map((option) => (
                    <button
                        key={option.amount}
                        className={`group cursor-pointer relative flex items-center justify-between p-5 rounded-2xl border-2 transition-all duration-300 ${option.featured
                                ? "border-indigo-600 bg-indigo-50/30 shadow-md"
                                : "border-gray-100 hover:border-indigo-200 hover:bg-gray-50"
                            }`}
                        onClick={() => setOffer(String(option.id))}
                    >
                        {option.featured && (
                            <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-indigo-600 text-white text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full shadow-sm">
                                Most Popular
                            </span>
                        )}

                        <div className="flex items-center gap-4">
                            <div className={`p-2.5 rounded-xl bg-[#2c81e3a8] text-white shadow-inner`}>
                                {option.icon}
                            </div>
                            <div className="text-left">
                                <h3 className="font-bold text-gray-900 flex items-center gap-2">
                                    {option.amount.toLocaleString()} <span className="text-xs text-gray-400 font-medium">Credits</span>
                                </h3>
                                <p className="text-xs text-gray-500 font-medium">{option.sub}</p>
                            </div>
                        </div>

                        <div className="flex flex-col items-end">
                            <span className={`text-sm font-bold ${option.featured ? "text-indigo-600" : "text-gray-400"} transition-transform`}>
                                Stake →
                            </span>
                        </div>
                    </button>
                ))}
            </div>
            <div className="px-8 pb-8 pt-2 text-center">
                <p className="text-[11px] text-gray-400 leading-relaxed">
                    *Staked credits are locked for 7 days and can be retrieved in the payments tab.
                </p>
            </div>
        </>
    );
}

function StakeScreen({ close, id }: { close: () => void, id: string }) {

    const [offer, setOffer] = useState<string | null>(null);
    const { authenticated } = useAuth();
    const [currentScreen, setCurrentScreen] = useState<"staking" | "authenticating" | "paying">("staking");

    const getScreen = () => {
        if (currentScreen == "staking") return <StakingScreen close={close} setOffer={setOffer} />;
        if (currentScreen == "authenticating") return <AuthenticationScreen close={close}/>;
        return <SubmissionScreen offer={offer as string} close={close} id={id}/>
    }
    
    useEffect(() => {

        if (offer) {
            if (authenticated) {
                setCurrentScreen("paying");
            } 
            else {
                setCurrentScreen("authenticating");
            }
        }

    }, [offer, authenticated])

    return createPortal(
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-slate-950/40 backdrop-blur-md flex items-center justify-center p-6"
        >
            <motion.div
                transition={{ type: "spring", damping: 25, stiffness: 300 }}
                className="relative bg-white rounded-3xl shadow-2xl max-w-md w-full overflow-hidden border border-gray-100"
            >
                {getScreen()}
            </motion.div>
        </motion.div>,
        document.body
    );
}

export default function AgentDetails({ agent }: { agent: Agent }) {

    const [staking, setStaking] = useState<boolean>(false);

    return (
        <>
            {
                staking && <StakeScreen close={() => setStaking(false)} id={agent.id}/>
            }
            <div className="space-y-4 relative">
                <div className="absolute -top-[5px] -right-[8px]">
                    Enjoy this server? <span onClick={() => setStaking(true)} className="px-2 py-0.2 bg-[#2c81e3a8] text-white hover:scale-105 duration-500 transition-all ease-in-out cursor-pointer inline-block rounded-full">Stake</span> to show your support!
                </div>
                <section>
                    <SectionTitle>Description</SectionTitle>
                    <p className="text-gray-600 leading-relaxed">{agent.description}</p>
                </section>
                <section>
                    <SectionTitle>Details</SectionTitle>
                    <div className="border-2 border-gray-400/40 rounded-xl px-4 divide-y divide-gray-200">
                        <CopyableField label="Agent ID" value={agent.id} />
                        <InfoRow label="Cost per Token">
                            <span className="text-[#2c81e3]">{agent.cost_per_token} credits</span>
                        </InfoRow>
                        <InfoRow label="Staked">
                            <span className="text-[#2c81e3] flex gap-2 items-center justify-center">{agent.staked}<Trophy size={16}/></span>
                        </InfoRow>
                        <InfoRow label="Date Created">
                            {
                                new Date(agent.date).toLocaleDateString("en-US", {
                                    year: "numeric",
                                    month: "long",
                                    day: "numeric",
                                })
                            }
                        </InfoRow>
                        {
                            agent.creator &&
                            <InfoRow label="Creator">
                                <span className="">{agent.creator}</span>
                            </InfoRow>
                        }
                    </div>
                </section>
                {
                    (agent.tools && Object.keys(agent.tools).length > 0) &&
                    <section>
                        <SectionTitle>
                            Tools
                            <span className="text-sm font-normal text-gray-400">
                                ({Object.keys(agent.tools).length})
                            </span>
                        </SectionTitle>
                        <div className="space-y-4">
                            {Object.entries(agent.tools).map(([name, docstring]) => (
                                <ToolDocstring key={name} name={name} docstring={docstring} />
                            ))}
                        </div>
                    </section>
                }
                <section>
                    <SectionTitle>
                        Code
                    </SectionTitle>
                    <pre className="border-2 border-gray-400/40 bg-gray-100 rounded-xl mt-3 rounded-lg bg-white font-mono p-4 text-sm text-black overflow-x-auto">
                        <code>
                            {agent.program.trim()}
                        </code>
                    </pre>
                </section>
            </div>
        </>
    );
}
