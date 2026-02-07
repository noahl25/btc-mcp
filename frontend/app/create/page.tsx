'use client'

import { File, Lock, Server, Sparkles, X } from 'lucide-react';
import { AnimatePresence, motion, useAnimationControls } from 'motion/react';
import { useState, useRef, useEffect } from 'react';
import axios, { AxiosResponse } from "axios";
import { useRouter } from 'next/navigation';
import QRCode from "qrcode";
import React from 'react';
import { useAuth } from '@/components/AuthContext';
import Loader from '@/components/Loader';

type FileInputProps = {
    icon: React.ReactNode,
    label: string,
    accept: string,
    file: File | null,
    onFileChange: (file: File | null) => void,
    required?: boolean
}

const FileInput = ({ icon, label, accept, file, onFileChange, required = true }: FileInputProps) => {

    const inputRef = useRef<HTMLInputElement>(null);

    const handleClick = () => {
        inputRef.current?.click();
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0] || null;
        onFileChange(selectedFile);
    };

    const handleRemove = (e: React.MouseEvent) => {
        e.stopPropagation();
        onFileChange(null);
        if (inputRef.current) {
            inputRef.current.value = '';
        }
    };

    return (
        <div onClick={handleClick} className={`relative group cursor-pointer aspect-square rounded-xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center ${file ? 'border-[#2c81e3] bg-[#2c81e3]/5' : 'border-gray-300 hover:border-[#2c81e3] hover:bg-[#2c81e3]/5'}`}>
            <input ref={inputRef} type="file" accept={accept} onChange={handleChange} className="hidden" />
            {
                file && <div onClick={(e) => { onFileChange(null); e.stopPropagation(); }} className='absolute group hover:bg-red-500/20 text-gray-400 hover:text-red-500 transition-all top-2 right-2 size-6 rounded-full bg-gray-400/10 grid place-items-center'>
                    <X className='' size={17} />
                </div>
            }
            {icon}
            {
                !file ?
                    <>
                        <span className='text-gray-400 group-hover:text-[#2c81e3] transition-all mt-2'>{label}</span>
                        <span className='text-gray-400/50 text-xs group-hover:text-[#2c81e3]/40 transition-all'>{required ? "Required" : "Optional"}</span>
                    </>
                    :
                    <>
                        <span className='text-gray-400 group-hover:text-[#2c81e3] transition-all mt-2'>{file.name}</span>
                        <span className='text-gray-400/50 text-xs group-hover:text-[#2c81e3]/40 transition-all'>{(file.size / 1000).toFixed(2)} kB</span>
                    </>
            }
        </div>
    );
}

const SteppedSlider = ({ steps, unit, setValue }: { steps: number[], unit: string, setValue: (value: number) => void }) => {

    const [level, setLevel] = useState<number>(0);
    const barRef = useRef<HTMLDivElement | null>(null);
    const constraintsRef = useRef<HTMLDivElement | null>(null);

    const handleDrag = (event: MouseEvent | TouchEvent | PointerEvent, info: { point: { x: number } }) => {
        if (!barRef.current) return;

        const barRect = barRef.current.getBoundingClientRect();
        const relativeX = info.point.x - barRect.left;
        const percentage = Math.max(0, Math.min(1, relativeX / barRect.width));
        const newLevel = Math.round(percentage * (steps.length - 1));

        setLevel(newLevel);
    };

    const handleStepClick = (index: number) => {
        setLevel(index);
        setValue(steps[index]);
    };

    const sliderPosition = (level / (steps.length - 1)) * 100;

    return (
        <div ref={constraintsRef} className='w-full relative px-2'>
            <div ref={barRef} className='w-full bg-gray-300 rounded-full h-2 relative'>
                <motion.div
                    className='absolute top-0 bottom-0 left-0 bg-[#2c81e3] rounded-full'
                    animate={{ width: `${sliderPosition}%` }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
                {
                    steps.map((val, key) => (
                        <div key={key} onClick={() => handleStepClick(key)} className='absolute top-1/2 -translate-y-1/2 -translate-x-1/2 cursor-pointer z-10' style={{ left: `${(key / (steps.length - 1)) * 100}%` }}>
                            <motion.div
                                className={`size-3 rounded-full transition-colors duration-200 ${level >= key ? "bg-[#2c81e3]" : "bg-gray-300"}`}
                                whileHover={{ scale: 1.2 }}
                                whileTap={{ scale: 0.9 }}
                            />
                            <span className='absolute -translate-x-1/2 left-1/2 top-4 text-sm text-gray-400 select-none'>
                                {val}{unit}
                            </span>
                        </div>
                    ))
                }
            </div>
        </div>
    );
}


const SubmissionScreen = ({ state, onClose }: { state: AxiosResponse<any, any, {}> | null, onClose: () => void }) => {

    const [loadingState, setLoadingState] = useState<"loading" | "complete" | "failed">("loading");

    useEffect(() => {

        if (state != null) {
            if (state?.status != 200) {
                setLoadingState("failed");
            }
            else {
                setLoadingState("complete");
            }
        }

        console.log(state)

    }, [state])

    const router = useRouter();

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ ease: "easeInOut", duration: 0.6 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6">
            <div className="bg-white relative rounded-2xl shadow-2xl max-w-md w-full h-60 relative">
                <div className='mt-7'>
                    <div className='mx-auto w-fit mb-5 relative translate-y-2'>
                        <Loader state={loadingState} />
                    </div>
                    <AnimatePresence mode="wait">
                        {
                            loadingState == "loading" ?
                            <motion.div 
                                key="loading"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 0.5 }}
                                className='flex flex-col items-center pt-5'
                            >
                                <div className='text-gray-800 text-lg'>Launching your agent now.</div>
                                <div className='text-gray-400 text-sm'>This may take a moment.</div>
                            </motion.div>
                            : 
                            loadingState == "complete" ?
                            <motion.div
                                key="complete"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1}}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 0.5 }}
                                className='flex flex-col items-center'
                            >
                                <div className='text-gray-800 text-lg text-center mb-4'>Success!</div>
                                <div className='flex gap-4 justify-center items-center'>
                                    <div onClick={() => router.push(`/explore/${state?.data.message}`)} className="hover:scale-110 active:scale-90 py-1 px-3 cursor-pointer text-white flex gap-1.5 transition-all duration-500 ease-in-out bg-[#2c81e3a8] rounded-full items-center justify-center">
                                        <div className='text-sm'>See your agent</div>
                                    </div>
                                    <div onClick={onClose} className="hover:scale-110 active:scale-90 py-1 px-3 cursor-pointer text-gray-500 border-gray-500 border-2 flex gap-1.5 transition-all duration-500 ease-in-out rounded-full items-center justify-center">
                                        <div className='text-sm'>Create another</div>
                                    </div>
                                </div>
                            </motion.div>
                            :
                            <motion.div
                                key="failed"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 0.5 }}
                                className='flex flex-col items-center'
                            >
                                <div className='text-gray-800 text-lg text-center'>Failed.</div>
                                <span className='text-sm text-red-500 mb-2 px-2 text-center'>{state?.data.error ?? "An unkown error occured."}</span>
                                <div className="hover:scale-110 active:scale-90 py-1 w-fit px-3 cursor-pointer text-white flex gap-1.5 transition-all duration-500 ease-in-out bg-red-500 rounded-full items-center justify-center">
                                    <div onClick={onClose} className='text-sm'>Go back</div>
                                </div>
                            </motion.div>
                        }
                    </AnimatePresence>
                </div>
            </div>
        </motion.div>
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
                    setTimeout(close, 750);
                });
            }, 500);
            return () => clearTimeout(timeout);
        }

    }, [complete]);
    
    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6">
            <div className="bg-white relative rounded-2xl py-3 px-5 shadow-2xl flex flex-col items-center justify-center w-[350px] h-[350px] overflow-hidden">
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
                        <div className='text-center text-gray-800'>
                            <div>
                                Authenticate using your Lightning wallet.
                            </div>
                            <div className='text-xs text-gray-400'>
                                This will be used to verify the ownership of your agent.
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
            </div>
        </motion.div>
    );
}

type ErrorField = "file" | "other" | "title" | "description";
type ErrorMap = Map<ErrorField, string[]>;

export default function Create() {

    const [server, setServer] = useState<File | null>(null);
    const [requirements, setRequirements] = useState<File | null>(null);
    const [environment, setEnvironment] = useState<File | null>(null);
    const [title, setTitle] = useState<string | null>(null);
    const [description, setDescription] = useState<string | null>(null);
    const [isPrivate, setIsPrivate] = useState<boolean>(false);
    const [cpu, setCPU] = useState<number>(25);
    const [memory, setMemory] = useState<number>(128);
    const [storage, setStorage] = useState<number>(1024);
    const [sats, setSats] = useState<number>(0.05);
    const [errors, setErrors] = useState<ErrorMap>(new Map());
    const [submission, setSubmission] = useState<AxiosResponse<any, any, {}> | null>(null);
    const [submitted, setSubmitted] = useState<boolean>(false);
    
    const [showAuthenticationScreen, setShowAuthenticationScreen] = useState<boolean>(false);

    useEffect(() => {

        const cpuCostPerPercent = 0.002;
        const memoryCostPerMB = 0.0001;
        const storageCostPerMB = 0.00002;

        const totalCost = Math.max((cpu * cpuCostPerPercent) + (memory * memoryCostPerMB) + (storage * storageCostPerMB), 0.1);
        setSats(totalCost);

    }, [cpu, memory, storage])

    const onSubmit = async () => {

        let hasError = false;
        const accumulated: ErrorMap = new Map();

        const addError = (field: ErrorField, message: string) => {
            const existing = accumulated.get(field) ?? [];
            accumulated.set(field, [...existing, message]);
            hasError = true;
        }

        if (!server) {
            addError("file", "Please add a server file.");
        }
        else if (server.size > 1073741824) {
            addError("file", "Server must be less than 1GB.");
        }
        if (requirements && requirements.size > 1073741824) {
            addError("other", "Requirements must be less than 1GB.");
        }
        else if (environment && environment.size > 1073741824) {
            addError("other", "Environment must be less than 1GB.");
        }
        if (title == null || title.length === 0) {
            addError("title", "Please add a title.");
        }
        else if (title.length > 30) {
            addError("title", "Title must be between 1 and 30 characters.");
        }
        if (description == null || description.length === 0) {
            addError("description", "Please add a description.");
        }
        else if (description.length > 30) {
            addError("description", "Description must be between 1 and 30 characters.");
        }
        if (hasError) {
            setErrors(prev => {
                const newMap = new Map(prev);
                accumulated.forEach((messages, field) => {
                    const existing = newMap.get(field) ?? [];
                    newMap.set(field, [...existing, ...messages]);
                });
                return newMap;
            });
            return;
        }

        setErrors(new Map());

        const res = await axios.get("http://localhost:8000/creator/session", {
            withCredentials: true
        });
        if (!res.data.authenticated) {
            setShowAuthenticationScreen(true);
            return;
        }

        const formData = new FormData();
        if (server) formData.append("mcp", server);
        if (requirements) formData.append("requirements", requirements);
        if (environment) formData.append("env", environment);
        if (title) formData.append("title", title);
        if (description) formData.append("description", description);
        formData.append("private", String(isPrivate));
        formData.append("cpu", String(cpu));
        formData.append("ram", String(memory));
        formData.append("tmpfs", String(storage));

        setSubmitted(true);
        try {
            const response = await axios.post("http://localhost:8000/api/deploy", formData, {
                headers: { "Content-Type": "multipart/form-data" },
                withCredentials: true
            });
            setSubmission(response);
        } catch (error: any) {
            setSubmission(error.response || {
                status: 500,
                data: { error: error.message || "Unknown error" }
            });
        }

    }

    const router = useRouter();

    return (
        <div className="w-full relative pt-[100px]">
            {
                submitted && <SubmissionScreen state={submission} onClose={() => { setSubmitted(false); setSubmission(null); }} />
            }
            {
                showAuthenticationScreen && <AuthenticationScreen close={() => {
                    setShowAuthenticationScreen(false);
                    onSubmit();
                }}/>
            }
            <div className="fixed z-10 px-4 md:px-20 flex items-center justify-center flex-col md:items-end left-0 shadow-2xl/50 right-0 bottom-0 h-[100px] bg-white">
                <div className="text-sm md:text-lg text-gray-800">Estimated cost per input/output token: <span className="font-bold text-gray-800">{(sats/5).toFixed(2)}/{sats.toFixed(2)} credits</span></div>
                <div className="text-sm md:text-lg text-gray-800">Your cut per input/output token: <span className="font-bold text-gray-800">0.01/0.05 credits</span></div>
            </div>
            <div className="mx-auto w-fit text-[40px] sm:text-[60px] text-white">
                <div>Create an agent.</div>
            </div>
            <div className="max-w-5xl mx-auto px-6 pb-[150px]">
                <div className="bg-white/90 backdrop-blur-md rounded-2xl mt-[45px] shadow-xl/10 py-6 px-8">
                    <div className="flex gap-2 items-center justify-center sm:justify-start mb-4 text-nowrap">
                        <h2 className="text-md sm:text-xl text-gray-800">Upload Files</h2>
                        <span className="text-gray-800 text-md self-center">or</span>
                        <div className="hover:scale-105 py-1 px-3 cursor-pointer text-white flex gap-1.5 transition-all duration-300 ease-in-out bg-[#2c81e3a8] rounded-full items-center justify-center">
                            <Sparkles size={16} strokeWidth={2} />
                            <div className=''>Create with AI</div>
                        </div>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-2">
                        <FileInput
                            icon={<Server className='text-gray-400 group-hover:text-[#2c81e3] transition-all' size={30} />}
                            label="Server"
                            accept=".py,.txt"
                            file={server}
                            onFileChange={(file: File | null) => setServer(file)}
                        />
                        <FileInput
                            icon={<File className='text-gray-400 group-hover:text-[#2c81e3] transition-all' size={30} />}
                            label="Requirements"
                            accept=".txt"
                            file={requirements}
                            onFileChange={(file: File | null) => setRequirements(file)}
                            required={false}
                        />
                        <FileInput
                            icon={<Lock className='text-gray-400 group-hover:text-[#2c81e3] transition-all' size={30} />}
                            label="Environment"
                            accept=".env"
                            file={environment}
                            onFileChange={(file: File | null) => setEnvironment(file)}
                            required={false}
                        />
                    </div>
                    {
                        (errors.get("file") || errors.get("other")) &&
                        <div className="mb-4">
                            {errors.get("file")?.map((msg, i) => (
                                <p key={`file-${i}`} className="text-red-500 text-sm">{msg}</p>
                            ))}
                            {errors.get("other")?.map((msg, i) => (
                                <p key={`other-${i}`} className="text-red-500 text-sm">{msg}</p>
                            ))}
                        </div>

                    }
                    <div className='mb-6'></div>
                    <div className="text-nowrap mb-6">
                        <h2 className="text-md sm:text-xl text-gray-800">Title</h2>
                        <span className='text-gray-800/50 text-xs sm:text-base block mb-2'>Give your agent a short, memorable name.</span>
                        <div className='relative'>
                            <input
                                type="text"
                                placeholder="Title..."
                                className={`w-full px-4 py-2.5 rounded-xl border-2 ${errors.get("title") ? 'border-red-500' : 'border-gray-300'} focus:border-[#2c81e3] focus:outline-none transition-colors text-gray-800 placeholder:text-gray-400`}
                                onChange={(e) => setTitle(prev => e.target.value.length > 30 ? prev : e.target.value)}
                                maxLength={30}
                            />
                            <div className='absolute bottom-[105%] right-1'>
                                <span className='text-gray-800/50'>{title?.length ?? 0}/30</span>
                            </div>
                        </div>
                        {
                            errors.get("title")?.map((msg, i) => (
                                <p key={`title-${i}`} className="text-red-500 text-sm mt-1">{msg}</p>
                            ))
                        }
                    </div>
                    <div className="mb-6 text-nowrap">
                        <h2 className="text-md sm:text-xl text-gray-800">Description</h2>
                        <span className='text-gray-800/50 text-xs sm:text-base block mb-2'>Let others know what your agent can do.</span>
                        <div className={`relative w-full pl-4 pr-2 py-2.5 rounded-xl border-2 ${errors.get("description") ? 'border-red-500' : 'border-gray-300'} focus-within:border-[#2c81e3]`}>
                            <textarea
                                placeholder="Description..."
                                rows={4}
                                className="w-full scrollbar focus:outline-none transition-colors text-gray-800 placeholder:text-gray-400 resize-none"
                                maxLength={500}
                                onChange={(e) => setDescription(prev => e.target.value.length > 500 ? prev : e.target.value)}
                            />
                            <div className='absolute bottom-[105%] right-1'>
                                <span className='text-gray-800/50'>{description?.length ?? 0}/500</span>
                            </div>
                        </div>
                        {
                            errors.get("description")?.map((msg, i) => (
                                <p key={`desc-${i}`} className="text-red-500 text-sm mt-1">{msg}</p>
                            ))
                        }
                    </div>
                    <div className="mb-6">
                        <h2 className="text-md sm:text-xl text-gray-800">Private</h2>
                        <span className='text-gray-800/50 text-xs sm:text-base block mb-3'>Require Lightning authentication before accessing your agent.</span>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setIsPrivate(true)}
                                className={`px-4 py-2 rounded-xl border-2 text-sm cursor-pointer transition-all duration-300 ${isPrivate ? 'border-[#2c81e3] bg-[#2c81e3]/10 text-[#2c81e3]' : 'border-gray-300 text-gray-400 hover:border-[#2c81e3] hover:text-[#2c81e3]'}`}
                            >
                                Yes
                            </button>
                            <button
                                onClick={() => setIsPrivate(false)}
                                className={`px-4 py-2 rounded-xl border-2 text-sm transition-all cursor-pointer duration-300 ${!isPrivate ? 'border-[#2c81e3] bg-[#2c81e3]/10 text-[#2c81e3]' : 'border-gray-300 text-gray-400 hover:border-[#2c81e3] hover:text-[#2c81e3]'}`}
                            >
                                No
                            </button>
                        </div>
                    </div>
                    <div className="mb-12">
                        <h2 className="text-md sm:text-xl text-gray-800">CPU</h2>
                        <span className='text-gray-800/50 text-xs sm:text-base block mb-3'>Choose how much processing power your agent can use.</span>
                        <SteppedSlider steps={[25, 50, 75, 100]} unit="%" setValue={setCPU} />
                    </div>
                    <div className="mb-12">
                        <h2 className="text-md sm:text-xl text-gray-800">Memory</h2>
                        <span className='text-gray-800/50 text-xs sm:text-base block mb-3'>The amount of RAM your agent has access to.</span>
                        <SteppedSlider steps={[128, 352, 576, 800, 1024]} unit="MB" setValue={setMemory} />
                    </div>
                    <div className="mb-12">
                        <h2 className="text-md sm:text-xl text-gray-800">Storage</h2>
                        <span className='text-gray-800/50 text-xs sm:text-base block mb-3'>Set the disk space your agent can use for data and files.</span>
                        <SteppedSlider steps={[1024, 2048, 3072, 4096, 5120]} unit="MB" setValue={setStorage} />
                    </div>
                    <div className='flex gap-5 justify-center items-center w-full'>
                        <div onClick={onSubmit} className="hover:scale-110 active:scale-90 py-1 px-3 cursor-pointer text-white flex gap-1.5 transition-all duration-500 ease-in-out bg-[#2c81e3a8] rounded-full items-center justify-center">
                            <div className=''>Continue</div>
                        </div>
                        <div className="hover:scale-110 active:scale-90 py-1 px-3 cursor-pointer text-gray-500 border-gray-500 border-2 flex gap-1.5 transition-all duration-500 ease-in-out rounded-full items-center justify-center">
                            <div className=''>Preview</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}